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

func InsertSemanticPaperIntoDB(ctx context.Context, dbPool *pgxpool.Pool, semanticPaperApiKey, query string, limit uint64, offset uint64) error {
	client := &http.Client{}

	req, err := http.NewRequest("GET", buildSemanticURL(query, limit, offset), nil)
	if err != nil {
		log.Println("creating a new GET req failed")
		return err
	}

	// semanticPaperApiKey := os.Getenv("SEMANTIC_PAPER_API_KEY")
	// if semanticPaperApiKey == "" {
	// 	log.Println("SemanticPaper api key missing")
	// 	return errors.New("semanticPaperApiKey missing")
	// }
	req.Header.Add("x-api-key", semanticPaperApiKey)

	res, err := client.Do(req)
	if err != nil {
		log.Printf("GET request failed: %v\n", err)
		return err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("semantic scholar returned non-200 status: %s", res.Status)
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed to read response body: %v\n", err)
		return err
	}

	var resp SemanticSearchResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		log.Printf("Failed to parse JSON: %v\n", err)
		return err
	}

	for _, semanticPaper := range resp.Data {
		researchPaper, err := getResearchPaperFromSemantic(semanticPaper)

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

func getResearchPaperFromSemantic(p SemanticPaper) (db.ResearchPaper, error) {
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
	}

	return paper, nil
}
