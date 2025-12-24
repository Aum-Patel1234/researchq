package researchpaperapis

import (
	"context"
	"encoding/json"
	"encoding/xml"
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

const baseURL = "https://export.arxiv.org/api/query?search_query=all:%s&start=%d&max_results=%d"

func buildArxivURL(query string, start uint64, maxResults uint64) string {
	q := url.QueryEscape(query) // e.g. "machine learning" → "machine+learning"
	return fmt.Sprintf(baseURL, q, start, maxResults)
}

// func filerResponse(jsonData string) (ArxivEntry, error) {
// 	var entry ArxivEntry
//
// 	err := json.Unmarshal([]byte(jsonData), &entry)
// 	if err != nil {
// 		return entry, err
// 	}
//
// 	return entry, nil
// }
//
// func filterPdfLink(paperLink string) string {
// 	return strings.Replace(paperLink, "/abs/", "/pdf/", 1)
// }

func GetPDFLink(entry ArxivEntry) string {
	for _, l := range entry.Link {
		if l.Type == "application/pdf" || l.Title == "pdf" {
			return l.Href
		}
	}
	return ""
}

func MakeArivAPICALL(ctx context.Context, query string, start, maxResults uint64) (Feed, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, buildArxivURL(query, start, maxResults), nil)
	if err != nil {
		return Feed{}, fmt.Errorf("failed to create arxiv request: %w", err)
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return Feed{}, fmt.Errorf("arxiv GET request failed: %w", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return Feed{}, fmt.Errorf("arxiv returned non-200 status: %s", res.Status)
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed to read response body: %v\n", err)
		return Feed{}, err
	}

	var feed Feed
	if err := xml.Unmarshal(body, &feed); err != nil {
		log.Printf("Failed to parse XML: %v\n", err)
		return Feed{}, err
	}

	return feed, nil
}

func InsertArxivEntryToDB(ctx context.Context, dbPool *pgxpool.Pool, query string, start, maxResults uint64) error {
	feed, err := MakeArivAPICALL(ctx, query, start, maxResults)
	if err != nil {
		return err
	}

	for _, entry := range feed.Entries {
		researchPaper, err := getResearchPaperFromArxivEntry(&entry, query)
		if err != nil {
			log.Printf("[ARXIV] skipping entry id=%s: %v", entry.ID, err)
			continue
		}

		if strings.TrimSpace(researchPaper.PDFURL) == "" {
			log.Printf("[ARXIV] skipping paperId=%s: empty PDF URL", entry.ID)
			continue
		}

		if err := db.InsertIntoDb(ctx, dbPool, researchPaper); err != nil {
			log.Printf("[DB] failed inserting arxiv paper id=%s title=%q: %v", entry.ID, researchPaper.Title, err)
			continue
		}
	}

	return nil
}

func getResearchPaperFromArxivEntry(entry *ArxivEntry, query string) (db.ResearchPaper, error) {
	if entry == nil {
		return db.ResearchPaper{}, errors.New("nil entry")
	}

	title := strings.TrimSpace(entry.Title)
	if title == "" {
		return db.ResearchPaper{}, errors.New("missing title in entry")
	}

	pdfURL := GetPDFLink(*entry)
	if pdfURL == "" {
		return db.ResearchPaper{}, fmt.Errorf("no pdf/url found for entry id=%s title=%s", entry.ID, title)
	}

	var sourceID *string
	if s := strings.TrimSpace(entry.ID); s != "" {
		sourceID = &s
	}

	authors := make([]string, 0, len(entry.Author))
	for _, author := range entry.Author {
		name := strings.TrimSpace(author.Name)
		authors = append(authors, name)
	}

	authorsJSON, err := json.Marshal(authors)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal authors: %w", err)
	}

	// Metadata: marshal the whole entry for raw payload (useful later)
	metadataJSON, err := json.Marshal(entry)
	if err != nil {
		return db.ResearchPaper{}, fmt.Errorf("failed to marshal metadata: %w", err)
	}

	var doiPtr *string
	if d := strings.TrimSpace(entry.ArxivDOI); d != "" {
		doiPtr = &d
	}

	paper := db.ResearchPaper{
		Source:   db.Arxiv,
		SourceID: sourceID,
		Title:    title,
		PDFURL:   pdfURL,
		DOI:      doiPtr,
		Authors:  &authorsJSON,
		Metadata: &metadataJSON,
		Topic:    query,
	}

	return paper, nil
}
