package main

import (
	"context"
	"fmt"
	"go_ingestion/db"
	researchpaperapis "go_ingestion/internal/research_paper_apis"
	"log"

	"github.com/joho/godotenv"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
		return
	}

	conn := db.ConnectToDb()
	defer conn.Close(context.Background())

	// temp
	arxivEntries, err := researchpaperapis.GetArxivResponse("nlp")
	if err != nil {
		fmt.Println("GET req failed")
		return
	}

	var pdfLinks []string
	for _, e := range arxivEntries {
		pdfURL := researchpaperapis.GetPDFLink(e)
		fmt.Println(e.ID)
		if pdfURL != "" {
			pdfLinks = append(pdfLinks, pdfURL)
		}
	}
	fmt.Println("\n\n", pdfLinks)

	for _, link := range pdfLinks {
		fmt.Println(link)
	}
	// temp

	fmt.Println("Executed Successfully")
}
