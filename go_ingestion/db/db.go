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

// -- Minimal enum for source
// CREATE TYPE IF NOT EXISTS paper_source AS ENUM ('arxiv','semanticscholar','springernature');
//
// -- Very minimal research_papers table
// CREATE TABLE IF NOT EXISTS research_papers (
//     id BIGSERIAL PRIMARY KEY,        -- auto-increment ID
//     source paper_source NOT NULL,    -- source of the record
//     source_id TEXT,                  -- original source ID (e.g. "2104.12405v2")
//     title TEXT NOT NULL,             -- required
//     pdf_url TEXT NOT NULL,           -- required for retrieval
//     authors JSONB,                   -- optional
//     doi TEXT,                        -- optional
//     metadata JSONB,                  -- optional raw payload
//     created_at TIMESTAMPTZ DEFAULT now()
// );
//
// -- Optional: minimal indexes (only if you plan to filter by source or DOI)
// CREATE INDEX IF NOT EXISTS idx_research_papers_source ON research_papers(source);
//
// ALTER TABLE research_papers
// ADD COLUMN IF NOT EXISTS embedding_processed BOOLEAN DEFAULT false;

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

	fmt.Printf("Inserted paper with ID %d at %s\n", paper.ID, paper.CreatedAt)
	return err
}
