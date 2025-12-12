package main

import (
	"context"
	"fmt"
	"go_ingestion/db"
	researchpaperapis "go_ingestion/internal/research_paper_apis"
	"log"
	"os"

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

	// arxiv
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
	// arxiv

	fmt.Println("\n------------")
	pdfLinks = pdfLinks[:0] // reset

	// semantic
	semantic, err := researchpaperapis.GetSemanticPapers("nlp", 5)
	if err != nil {
		fmt.Println("GET req failed")
		return
	}

	for _, e := range semantic {
		pdfURL := researchpaperapis.GetSemanticPDFLink(e)
		fmt.Println(e.Title)
		if pdfURL != "" {
			pdfLinks = append(pdfLinks, pdfURL)
		}
	}
	fmt.Println("\n\n", pdfLinks)

	for _, link := range pdfLinks {
		fmt.Println(link)
	}
	// !semantic

	fmt.Println("\n------------")
	pdfLinks = pdfLinks[:0] // reset

	// springer
	springer, err := researchpaperapis.GetSpringerResponse("nlp", os.Getenv("SPRINGER_NATURE_META_APIKEY"))
	if err != nil {
		fmt.Println("GET req failed")
		return
	}

	for _, e := range springer {
		pdfURL := researchpaperapis.GetSpringerPDF(e)
		fmt.Println(e.Title)
		if pdfURL != "" {
			pdfLinks = append(pdfLinks, pdfURL)
		}
	}
	fmt.Println("\n\n", pdfLinks)

	for _, link := range pdfLinks {
		fmt.Println(link)
	}
	// !apringer

	fmt.Println("Executed Successfully")
}
