package main

import (
	"context"
	"go_ingestion/db"
	"go_ingestion/internal/pipeline"
	"log"
	"os"
	"time"

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

	// ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	// defer stop()

	const query = "natural language preprocessing"

	var semanticScholarApiKey = os.Getenv("SEMANTIC_PAPER_API_KEY")
	var springerNatureApiKey = os.Getenv("SPRINGER_NATURE_META_APIKEY")
	if semanticScholarApiKey == "" || springerNatureApiKey == "" {
		log.Fatal("Required API keys are missing. Exiting...")
	}

	const arXivlimit = 25
	const semanticScholarLimit = 25
	const springerNatureLimit = 25

	// Fetch totals with a short-lived context
	totalsCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	totalArxivPapers, totalSemanticScholarPapers, totalSpringerNaturePapers := pipeline.GetTotalPapers(totalsCtx, query, semanticScholarApiKey, springerNatureApiKey, 1, 0)
	processedArxivPapers, processedSemanticPapers, processedSpringerNaturePapers := db.GetCurrentlyProcessedDocuments(totalsCtx, dbPool)
	time.Sleep(5 * time.Second)

	log.Printf(
		"[TOTALS] arXiv=%d (processed=%d) semantic=%d (processed=%d) springer=%d (processed=%d)",
		totalArxivPapers, processedArxivPapers,
		totalSemanticScholarPapers, processedSemanticPapers,
		totalSpringerNaturePapers, processedSpringerNaturePapers,
	)

	// var wg sync.WaitGroup
	// wg.Add(3)
	//
	// // NOTE: API limit reached
	// go func() {
	// 	defer wg.Done()
	// 	log.Println("[ARXIV] worker started")
	// 	pipeline.StartArxivProcess(ctx, dbPool, query, processedArxivPapers, totalArxivPapers, arXivlimit)
	// 	log.Println("[ARXIV] worker finished")
	// }()
	//
	// // NOTE: Its limit is reached
	// go func() {
	// 	defer wg.Done()
	// 	log.Println("[SEMANTIC] worker started")
	// 	pipeline.StartSemanticProcess(ctx, dbPool, semanticScholarApiKey, query, processedSemanticPapers, totalSemanticScholarPapers, semanticScholarLimit)
	// 	log.Println("[SEMANTIC] worker finished")
	// }()
	//
	// go func() {
	// 	defer wg.Done()
	// 	log.Println("[SPRINGER] worker started")
	// 	pipeline.StartSpringerProcess(ctx, dbPool, springerNatureApiKey, query, processedSpringerNaturePapers, totalSpringerNaturePapers, springerNatureLimit)
	// 	log.Println("[SPRINGER] worker finished")
	// }()
	//
	// wg.Wait()

	log.Println("All ingestion pipelines completed")
}
