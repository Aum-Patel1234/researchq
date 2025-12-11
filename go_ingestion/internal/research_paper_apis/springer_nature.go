package researchpaperapis

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
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
