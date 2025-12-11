package researchpaperapis

import (
	"encoding/json"
	"encoding/xml"
	"fmt"
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
