package researchpaperapis

import (
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
)

const baseURL = "https://export.arxiv.org/api/query?search_query=all:%s&start=%d&max_results=%d"

func buildArxivURL(query string, start int, maxResults int) string {
	q := url.QueryEscape(query) // e.g. "machine learning" → "machine+learning"
	return fmt.Sprintf(baseURL, q, start, maxResults)
}

func filerResponse(jsonData string) (ArxivEntry, error) {
	var entry ArxivEntry

	err := json.Unmarshal([]byte(jsonData), &entry)
	if err != nil {
		return entry, err
	}

	return entry, nil
}

func filterPdfLink(paperLink string) string {
	return strings.Replace(paperLink, "/abs/", "/pdf/", 1)
}
func GetPDFLink(entry ArxivEntry) string {
	for _, l := range entry.Link {
		if l.Type == "application/pdf" || l.Title == "pdf" {
			return l.Href
		}
	}
	return ""
}

func GetArxivResponse(query string) ([]ArxivEntry, error) {
	res, err := http.Get(buildArxivURL(query, 0, 5))
	if err != nil {
		log.Printf("GET request failed: %v\n", err)
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Failed to read response body: %v\n", err)
		return nil, err
	}

	var feed Feed
	if err := xml.Unmarshal(body, &feed); err != nil {
		log.Printf("Failed to parse XML: %v\n", err)
		return nil, err
	}

	return feed.Entries, nil
}

func getResearchPaperFromArxivEntry(entry *ArxivEntry) (db.ResearchPaper, error) {
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
	}

	return paper, nil
}
