package pipeline

import (
	"context"
	researchpaperapis "go_ingestion/internal/research_paper_apis"
	"log"
	"strconv"
)

func GetTotalPapers(ctx context.Context, query, semanticScholarApiKey, springerNatureApiKey string, limit, offset uint64) (uint64, uint64, uint64) {
	arxivRes, err := researchpaperapis.MakeArivAPICALL(ctx, query, offset, limit)
	if err != nil {
		log.Fatal("[ARXIV] failed to fetch total papers:", err)
	}
	totalArxivPapers := arxivRes.TotalResults

	semanticScholarRes, err := researchpaperapis.MakeSemanticScholarAPICALL(ctx, semanticScholarApiKey, query, limit, offset)
	if err != nil {
		log.Fatal("[SEMANTIC SCHOLAR] failed to fetch total papers:", err)
	}
	totalSemanticScholarPapers := uint64(semanticScholarRes.Total)

	springerNatureRes, err := researchpaperapis.MakeSpringerNatureAPICALL(ctx, springerNatureApiKey, query, limit, offset)
	if err != nil {
		log.Fatal("[SPRINGER] failed to fetch total papers:", err)
	}

	if len(springerNatureRes.Result) == 0 {
		log.Fatal("[SPRINGER] empty result metadata")
	}
	totalSpringerNaturePapers, err := strconv.ParseUint(
		springerNatureRes.Result[0].Total,
		10,
		64,
	)
	if err != nil {
		log.Fatal("[SPRINGER] failed to parse total results:", err)
	}

	return totalArxivPapers, totalSemanticScholarPapers, totalSpringerNaturePapers
}
