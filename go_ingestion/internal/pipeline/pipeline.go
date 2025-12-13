package pipeline

import (
	"context"
	"fmt"
	researchpaperapis "go_ingestion/internal/research_paper_apis"
	"log"
	"strconv"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func GetTotalPapers(ctx context.Context, query, semanticScholarApiKey, springerNatureApiKey string, limit, offset uint64) (uint64, uint64, uint64) {
	var (
		totalArxivPapers           uint64
		totalSemanticScholarPapers uint64
		totalSpringerNaturePapers  uint64
	)

	var wg sync.WaitGroup

	wg.Add(3)
	errChan := make(chan error, 3)

	go func() {
		// fmt.Println("start ARXIV")
		defer wg.Done()
		arxivRes, err := researchpaperapis.MakeArivAPICALL(ctx, query, offset, limit)
		if err != nil {
			errChan <- fmt.Errorf("[ARXIV] %w", err)
			return
		}
		totalArxivPapers = arxivRes.TotalResults
		// fmt.Println("end ARXIV")
	}()

	go func() {
		// fmt.Println("start SEMANTIC")

		defer wg.Done()
		semanticScholarRes, err := researchpaperapis.MakeSemanticScholarAPICALL(ctx, semanticScholarApiKey, query, limit, offset)
		if err != nil {
			errChan <- fmt.Errorf("[SEMANTIC SCHOLAR] %w", err)
			return
		}
		totalSemanticScholarPapers = semanticScholarRes.Total

		// fmt.Println("end SEMANTIC")
	}()

	go func() {
		// fmt.Println("start SPRINGER")
		defer wg.Done()

		springerNatureRes, err := researchpaperapis.MakeSpringerNatureAPICALL(ctx, springerNatureApiKey, query, limit, offset)
		if err != nil {
			errChan <- fmt.Errorf("[SPRINGER] %w", err)
			return
		}

		if len(springerNatureRes.Result) == 0 {
			errChan <- fmt.Errorf("[SPRINGER] empty result metadata")
			return
		}

		totalSpringerNaturePapers, err = strconv.ParseUint(springerNatureRes.Result[0].Total, 10, 64)
		if err != nil {
			errChan <- fmt.Errorf("[SPRINGER] parse error: %w", err)
			return
		}

		// fmt.Println("end SPRINGER")
	}()

	wg.Wait()
	close(errChan)

	for err := range errChan {
		log.Fatal(err)
	}

	return totalArxivPapers, totalSemanticScholarPapers, totalSpringerNaturePapers
}

func StartArxivProcess(ctx context.Context, dbPool *pgxpool.Pool, query string, processedArxivPapers, totalArxivPapers, limit uint64) {
	const maxRetries = 10

	for processedArxivPapers < totalArxivPapers {
		select {
		case <-ctx.Done():
			log.Println("[ARXIV] context cancelled, stopping worker")
			return
		default:
		}

		var err error
		for attempt := 1; attempt <= maxRetries; attempt++ {
			err = researchpaperapis.InsertArxivEntryToDB(ctx, dbPool, query, processedArxivPapers, limit)

			time.Sleep(30 * time.Second)
			if err == nil {
				break
			}

			log.Printf("[ARXIV] error at offset=%d attempt=%d/%d: %v", processedArxivPapers, attempt, maxRetries, err)
		}

		if err != nil {
			log.Printf("[ARXIV] skipping offset=%d after %d failures", processedArxivPapers, maxRetries)
		}

		processedArxivPapers += limit
	}
}

func StartSemanticProcess(ctx context.Context, dbPool *pgxpool.Pool, semanticScholarApiKey, query string, processedSemanticPapers, totalSemanticScholarPapers, limit uint64) {
	const maxRetries = 10

	for processedSemanticPapers < totalSemanticScholarPapers {
		select {
		case <-ctx.Done():
			log.Println("[SEMANTIC] context cancelled, stopping worker")
			return
		default:
		}

		var err error
		for attempt := 1; attempt <= maxRetries; attempt++ {
			err = researchpaperapis.InsertSemanticPaperIntoDB(ctx, dbPool, semanticScholarApiKey, query, limit, processedSemanticPapers)

			time.Sleep(30 * time.Second)
			if err == nil {
				break
			}

			log.Printf("[SEMANTIC] error at offset=%d attempt=%d/%d: %v", processedSemanticPapers, attempt, maxRetries, err)
			time.Sleep(30 * time.Second)
		}

		if err != nil {
			log.Printf("[SEMANTIC] skipping offset=%d after %d failures", processedSemanticPapers, maxRetries)
		}

		processedSemanticPapers += limit
	}
}

func StartSpringerProcess(ctx context.Context, dbPool *pgxpool.Pool, springerNatureApiKey, query string, processedSpringerNaturePapers, totalSpringerNaturePapers, limit uint64) {
	const maxRetries = 10

	for processedSpringerNaturePapers < totalSpringerNaturePapers {
		select {
		case <-ctx.Done():
			log.Println("[SPRINGER] context cancelled, stopping worker")
			return
		default:
		}

		var err error
		for attempt := 1; attempt <= maxRetries; attempt++ {
			err = researchpaperapis.InsertSpringerPaperIntoDB(ctx, dbPool, springerNatureApiKey, query, limit, processedSpringerNaturePapers)

			time.Sleep(30 * time.Second)
			if err == nil {
				break
			}

			log.Printf("[SPRINGER] error at offset=%d attempt=%d/%d: %v", processedSpringerNaturePapers, attempt, maxRetries, err)
		}

		if err != nil {
			log.Printf("[SPRINGER] skipping offset=%d after %d failures", processedSpringerNaturePapers, maxRetries)
		}

		processedSpringerNaturePapers += limit
	}
}
