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

const semanticBaseURL = "https://api.semanticscholar.org/graph/v1/paper/search?query=%s&limit=%d&offset=%d&fields=paperId,title,abstract,year,authors,url,openAccessPdf,venue,publicationTypes,citationCount,referenceCount,fieldsOfStudy"

func buildSemanticURL(query string, limit uint64, offset uint64) string {
	q := url.QueryEscape(query)
	return fmt.Sprintf(semanticBaseURL, q, limit, offset)
}

func MakeSemanticScholarAPICALL(ctx context.Context, semanticPaperApiKey, query string, limit, offset uint64) (SemanticSearchResponse, error) {
	client := &http.Client{}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, buildSemanticURL(query, limit, offset), nil)
	if err != nil {
		return SemanticSearchResponse{}, err
	}

	req.Header.Add("x-api-key", semanticPaperApiKey)

	res, err := client.Do(req)
	if err != nil {
		return SemanticSearchResponse{}, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return SemanticSearchResponse{}, fmt.Errorf("semantic scholar returned non-200 status: %s", res.Status)
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return SemanticSearchResponse{}, fmt.Errorf("semantic scholar returned status %s", res.Status)
	}

	var resp SemanticSearchResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return SemanticSearchResponse{}, err
	}

	return resp, nil
}

func InsertSemanticPaperIntoDB(ctx context.Context, dbPool *pgxpool.Pool, semanticPaperApiKey, query string, limit uint64, offset uint64) error {
	resp, err := MakeSemanticScholarAPICALL(ctx, semanticPaperApiKey, query, limit, offset)
	if err != nil {
		return err
	}

	for _, semanticPaper := range resp.Data {
		researchPaper, err := getResearchPaperFromSemantic(semanticPaper, query)

		if err != nil {
			log.Printf("[SEMANTIC] skipping entry id=%d: %v", researchPaper.ID, err)
			continue
		}

		if strings.TrimSpace(researchPaper.PDFURL) == "" {
			log.Printf("[SEMANTIC] skipping paperId=%s: empty PDF URL", semanticPaper.PaperID)
			continue
		}

		if err := db.InsertIntoDb(ctx, dbPool, researchPaper); err != nil {
			log.Printf("[DB] failed inserting arxiv paper id=%d title=%q: %v", researchPaper.ID, researchPaper.Title, err)
			continue
		}
	}

	return nil
}

func GetSemanticPDFLink(paper SemanticPaper) string {
	if paper.OpenAccessPdf != nil && paper.OpenAccessPdf.URL != nil {
		// log.Println("pdf link semanticPaper - ", *paper.OpenAccessPdf.URL, "\t", paper.OpenAccessPdf.Status)
		return *paper.OpenAccessPdf.URL
	}
	return ""
}

func getResearchPaperFromSemantic(p SemanticPaper, query string) (db.ResearchPaper, error) {
	if strings.TrimSpace(p.Title) == "" {
		return db.ResearchPaper{}, errors.New("missing title in semantic paper")
	}

	pdfURL := GetSemanticPDFLink(p)
	if strings.TrimSpace(pdfURL) == "" {
		return db.ResearchPaper{}, fmt.Errorf("no PDF URL found for semantic paperId=%s", p.PaperID)
	}

	var sourceID *string
	if id := strings.TrimSpace(p.PaperID); id != "" {
		sourceID = &id
	}

	authorNames := make([]string, 0, len(p.Authors))
	for _, a := range p.Authors {
		name := strings.TrimSpace(a.URL)
		if name == "" {
			name = strings.TrimSpace(a.AuthorID)
		}
		authorNames = append(authorNames, name)
	}

	authorsJSON, err := json.Marshal(authorNames)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal semantic authors: %w", err)
	}

	metadataJSON, err := json.Marshal(p)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal semantic metadata: %w", err)
	}

	paper := db.ResearchPaper{
		Source:   db.SemanticScholar,
		SourceID: sourceID,
		Title:    strings.TrimSpace(p.Title),
		PDFURL:   pdfURL,
		DOI:      nil,
		Authors:  &authorsJSON,
		Metadata: &metadataJSON,
		Topic:    query,
	}

	return paper, nil
}
