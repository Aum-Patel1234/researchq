package researchpaperapis

import (
	"encoding/json"
	"errors"
	"fmt"
	"go_ingestion/db"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
)

const springerBaseURL = "http://api.springernature.com/meta/v2/json"

func buildSpringerURL(query, apiKey string, limit int) string {
	params := url.Values{}
	params.Set("q", query)
	params.Set("p", fmt.Sprintf("%d", limit))
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

func GetSpringerResponse(query, apiKey string) ([]Record, error) {
	fullURL := buildSpringerURL(query, apiKey, 5)

	res, err := http.Get(fullURL)
	if err != nil {
		log.Printf("Springer API request failed: %v\n", err)
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed reading Springer response: %v\n", err)
		return nil, err
	}

	resp, err := parseSpringerResponse(body)
	if err != nil {
		log.Printf("JSON parsing failed: %v\n", err)
		return nil, err
	}

	return resp.Records, nil
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
