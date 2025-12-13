package main

import (
	"context"
	"fmt"
	"go_ingestion/db"
	"go_ingestion/internal/pipeline"
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

	dbPool := db.ConnectToDb()
	defer dbPool.Close()

	const query = "natural language preprocessing"

	var semanticScholarApiKey = os.Getenv("SEMANTIC_PAPER_API_KEY")
	var springerNatureApiKey = os.Getenv("SPRINGER_NATURE_META_APIKEY")
	if semanticScholarApiKey == "" || springerNatureApiKey == "" {
		log.Fatal("Required API keys are missing. Exiting...")
	}

	// variables to store totalPapers, limit and offset
	const limit = 100
	// 	processedArxivPapers          uint64
	// var (
	// 	processedSemanticNaturePapers uint64
	// 	processedSpringerNaturePapers uint64
	// )

	totalArxivPapers, totalSemanticNaturePapers, totalSpringerNaturePapers := pipeline.GetTotalPapers(context.Background(), query, semanticScholarApiKey, springerNatureApiKey, 1, 0)
	fmt.Println(totalArxivPapers, "\t", totalSemanticNaturePapers, "\t", totalSpringerNaturePapers)

	fmt.Println("Executed Successfully")
}
