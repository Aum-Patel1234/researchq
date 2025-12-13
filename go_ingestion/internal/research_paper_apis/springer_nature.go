package researchpaperapis

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"go_ingestion/db"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

const springerBaseURL = "http://api.springernature.com/meta/v2/json"

func buildSpringerURL(query, apiKey string, limit, offset uint64) string {
	params := url.Values{}
	params.Set("q", query)
	params.Set("p", fmt.Sprintf("%d", limit))
	params.Set("s", fmt.Sprintf("%d", offset))
	params.Set("api_key", apiKey)

	return springerBaseURL + "?" + params.Encode()
}

func parseSpringerResponse(data []byte) (SpringerResponse, error) {
	var resp SpringerResponse
	err := json.Unmarshal(data, &resp)
	return resp, err
}

func GetSpringerPDF(record Record) string {
	for _, u := range record.URL {
		if u.Format == "pdf" {
			return u.Value
		}
	}
	return ""
}

func MakeSpringerNatureAPICALL(ctx context.Context, apiKey, query string, limit, offset uint64) (SpringerResponse, error) {
	fullURL := buildSpringerURL(query, apiKey, limit, offset)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, fullURL, nil)
	if err != nil {
		return SpringerResponse{}, fmt.Errorf("failed to create Springer request: %w", err)
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return SpringerResponse{}, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return SpringerResponse{}, fmt.Errorf("Springer Nature returned non-200 status: %s", res.Status)
	}
	body, err := io.ReadAll(res.Body)
	if err != nil {
		return SpringerResponse{}, err
	}

	resp, err := parseSpringerResponse(body)
	if err != nil {
		return SpringerResponse{}, err
	}

	return resp, nil
}

func InsertSpringerPaperIntoDB(ctx context.Context, dbPool *pgxpool.Pool, apiKey, query string, limit, offset uint64) error {
	resp, err := MakeSpringerNatureAPICALL(ctx, apiKey, query, limit, offset)
	if err != nil {
		return err
	}

	for _, record := range resp.Records {
		researchPaper, err := getResearchPaperFromSpringerNature(record)

		if err != nil {
			log.Printf("[SPRINGER] skipping entry id=%d: %v", researchPaper.ID, err)
			continue
		}

		if strings.TrimSpace(researchPaper.PDFURL) == "" {
			log.Printf("[SPRINGER] skipping paperId=%s: empty PDF URL", record.Identifier)
			continue
		}

		if err := db.InsertIntoDb(ctx, dbPool, researchPaper); err != nil {
			log.Printf("[DB] failed inserting arxiv paper id=%d title=%q: %v", researchPaper.ID, researchPaper.Title, err)
			continue
		}
	}

	return nil
}

func getResearchPaperFromSpringerNature(rec Record) (db.ResearchPaper, error) {
	title := strings.TrimSpace(rec.Title)
	if title == "" {
		return db.ResearchPaper{}, errors.New("missing title in springer record")
	}

	pdfURL := GetSpringerPDF(rec)
	if strings.TrimSpace(pdfURL) == "" {
		return db.ResearchPaper{}, fmt.Errorf("no PDF URL found for springer record identifier=%s", rec.Identifier)
	}

	var sourceID *string
	if id := strings.TrimSpace(rec.Identifier); id != "" {
		sourceID = &id
	}

	authorNames := make([]string, 0, len(rec.Creators))
	for _, c := range rec.Creators {
		name := strings.TrimSpace(c.Creator)
		if name != "" {
			authorNames = append(authorNames, name)
		}
	}

	authorsJSON, err := json.Marshal(authorNames)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal springer authors: %w", err)
	}

	metadataJSON, err := json.Marshal(rec)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal springer metadata: %w", err)
	}

	var doiPtr *string
	if d := strings.TrimSpace(rec.DOI); d != "" {
		doiPtr = &d
	}

	paper := db.ResearchPaper{
		Source:   db.SpringerNature,
		SourceID: sourceID,
		Title:    title,
		PDFURL:   pdfURL,
		DOI:      doiPtr,
		Authors:  &authorsJSON,
		Metadata: &metadataJSON,
	}

	return paper, nil
}
