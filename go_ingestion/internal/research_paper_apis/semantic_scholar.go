package researchpaperapis

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
)

const semanticBaseURL = "https://api.semanticscholar.org/graph/v1/paper/search?query=%s&limit=%d&fields=paperId,title,abstract,year,authors,url,openAccessPdf,venue,publicationTypes,citationCount,referenceCount,fieldsOfStudy"

func buildSemanticURL(query string, limit int) string {
	q := url.QueryEscape(query)
	return fmt.Sprintf(semanticBaseURL, q, limit)
}

func GetSemanticPapers(query string, limit int) ([]SemanticPaper, error) {
	res, err := http.Get(buildSemanticURL(query, limit))
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

	var resp SemanticSearchResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		log.Printf("Failed to parse JSON: %v\n", err)
		return nil, err
	}
	// if len(resp.Data) > 0 {
	// 	fmt.Println("First paper title:", resp.Data[0].Title)
	// } else {
	// 	fmt.Println("No papers found for query:", query)
	// }

	return resp.Data, nil
}

func GetSemanticPDFLink(paper SemanticPaper) string {
	if paper.OpenAccessPdf != nil && paper.OpenAccessPdf.URL != nil {
		return *paper.OpenAccessPdf.URL
	}
	return ""
}
