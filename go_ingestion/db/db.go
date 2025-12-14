package db

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func ConnectToDb() *pgxpool.Pool {
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		log.Fatal("DATABASE_URL not set in environment or .env file")
	}

	dbPool, err := pgxpool.New(context.Background(), databaseURL)

	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to connect to database: %v\n", err)
		os.Exit(1)
	}

	return dbPool
}

// CREATE TYPE paper_source AS ENUM (
//     'arxiv',
//     'semanticscholar',
//     'springernature'
// );
//
// CREATE TABLE research_papers (
//     id BIGSERIAL PRIMARY KEY,
//
//     source paper_source NOT NULL,
//     source_id TEXT UNIQUE,
//     title TEXT UNIQUE NOT NULL,
//     pdf_url TEXT UNIQUE NOT NULL,
//
//     authors JSONB,
//     doi TEXT,
//     metadata JSONB,
//     embedding_processed BOOLEAN DEFAULT false,
//     created_at TIMESTAMPTZ DEFAULT now()
// );
//
// CREATE INDEX idx_research_papers_source
//     ON research_papers(source);

type ResearchPaper struct {
	ID       uint64      `db:"id"`
	Source   PaperSource `db:"source"`
	SourceID *string     `db:"source_id"`
	Title    string      `db:"title"`
	PDFURL   string      `db:"pdf_url"`
	Authors  *[]byte     `db:"authors"` // store JSONB as []byte
	DOI      *string     `db:"doi"`
	Metadata *[]byte     `db:"metadata"` // store JSONB as []byte
	// EmbeddingProcessed bool        `db:"embedding_processed"`
	CreatedAt time.Time `db:"created_at"`
}

type PaperSource string

const (
	Arxiv           PaperSource = "arxiv"
	SemanticScholar PaperSource = "semanticscholar"
	SpringerNature  PaperSource = "springernature"
)

func InsertIntoDb(ctx context.Context, dbPool *pgxpool.Pool, paper ResearchPaper) error {
	query := `
		INSERT INTO research_papers (source, source_id, title, pdf_url, authors, doi, metadata)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, created_at;
	`

	err := dbPool.QueryRow(ctx, query, paper.Source, paper.SourceID, paper.Title, paper.PDFURL, paper.Authors, paper.DOI, paper.Metadata).Scan(&paper.ID, &paper.CreatedAt)

	if err != nil {
		return fmt.Errorf("failed to insert paper: %w", err)
	}

	// fmt.Printf("Inserted paper with ID %d at %s\n", paper.ID, paper.CreatedAt)
	return err
}

func GetCurrentlyProcessedDocuments(ctx context.Context, dbPool *pgxpool.Pool) (uint64, uint64, uint64) {
	var arxivCount, semanticCount, springerCount uint64

	query := `
		SELECT 
			COUNT(*) FILTER (WHERE source = $1) AS arxiv_count,
			COUNT(*) FILTER (WHERE source = $2) AS semantic_count,
			COUNT(*) FILTER (WHERE source = $3) AS springer_count
		FROM research_papers;
	`

	err := dbPool.QueryRow(ctx, query, string(Arxiv), string(SemanticScholar), string(SpringerNature)).Scan(&arxivCount, &semanticCount, &springerCount)

	if err != nil {
		// NOTE: I can return 0,0,0 but its just computaion waste
		log.Fatal("Do not proceed")
	}

	return arxivCount, semanticCount, springerCount
}
