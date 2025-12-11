package db

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/jackc/pgx/v5"
)

func ConnectToDb() *pgx.Conn {
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		log.Fatal("❌ DATABASE_URL not set in environment or .env file")
	}

	conn, err := pgx.Connect(context.Background(), databaseURL)

	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to connect to database: %v\n", err)
		os.Exit(1)
	}

	return conn
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
