package db

import (
	"context"
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"
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
//
// ALTER TABLE research_papers
// ADD COLUMN topic TEXT;
//
// UPDATE research_papers
// SET topic = 'natural language processing';
//
// ALTER TABLE research_papers
// ALTER COLUMN topic SET NOT NULL;
//
// CREATE INDEX idx_research_papers_topic
//     ON research_papers(topic);

type ResearchPaper struct {
	ID                 uint64      `db:"id"`
	Source             PaperSource `db:"source"`
	SourceID           *string     `db:"source_id"`
	Title              string      `db:"title"`
	PDFURL             string      `db:"pdf_url"`
	Authors            *[]byte     `db:"authors"` // store JSONB as []byte
	DOI                *string     `db:"doi"`
	Metadata           *[]byte     `db:"metadata"` // store JSONB as []byte
	EmbeddingProcessed bool        `db:"embedding_processed"`
	Topic              string      `db:"topic"`
	CreatedAt          time.Time   `db:"created_at"`
}

type PaperSource string

const (
	Arxiv           PaperSource = "arxiv"
	SemanticScholar PaperSource = "semanticscholar"
	SpringerNature  PaperSource = "springernature"
)

func InsertIntoDb(ctx context.Context, dbPool *pgxpool.Pool, paper ResearchPaper) error {
	query := `
		INSERT INTO research_papers (source, source_id, title, pdf_url, authors, doi, metadata, topic)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, created_at;
	`

	err := dbPool.QueryRow(ctx, query, paper.Source, paper.SourceID, paper.Title, paper.PDFURL, paper.Authors, paper.DOI, paper.Metadata, paper.Topic).Scan(&paper.ID, &paper.CreatedAt)

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
		log.Fatal("Do not proceed - ", err)
	}

	return arxivCount, semanticCount, springerCount
}

// NOTE: sql to csv
func GetFullData(ctx context.Context, dbPool *pgxpool.Pool) {
	// NOTE: order is imp
	query := `
		SELECT
			id,
			source,
			source_id,
			title,
			pdf_url,
			authors,
			doi,
			metadata,
			embedding_processed,
			topic,
			created_at
		FROM research_papers;
		`

	rows, err := dbPool.Query(ctx, query)

	if err != nil {
		log.Fatal("Do not proceed - ", err)
	}
	defer rows.Close()

	if err := os.MkdirAll("data", 0755); err != nil {
		// IMPORTANT: 0755 = file permissions
		// ls -la = rwxr-xr-x
		// 7 → owner: read + write + execute
		// 5 → group: read + execute
		// 5 → others: read + execute
		log.Fatal("Failed to create data directory:", err)
	}

	file, err := os.Create("data/data.csv")
	if err != nil {
		log.Fatal("Failed to create CSV file:", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	writer.Write([]string{
		"id", "source", "source_id", "title", "pdf_url",
		"authors", "doi", "metadata",
		"embedding_processed", "topic", "created_at",
	})

	for rows.Next() {
		var paper ResearchPaper

		err := rows.Scan(
			&paper.ID,
			&paper.Source,
			&paper.SourceID,
			&paper.Title,
			&paper.PDFURL,
			&paper.Authors,
			&paper.DOI,
			&paper.Metadata,
			&paper.EmbeddingProcessed,
			&paper.Topic,
			&paper.CreatedAt,
		)
		if err != nil {
			log.Fatal("Row scan failed:", err)
		}

		writer.Write([]string{
			strconv.FormatUint(paper.ID, 10),
			string(paper.Source),
			nullableString(paper.SourceID),
			paper.Title,
			paper.PDFURL,
			byteSliceToString(paper.Authors),
			nullableString(paper.DOI),
			byteSliceToString(paper.Metadata),
			strconv.FormatBool(paper.EmbeddingProcessed),
			paper.Topic,
			paper.CreatedAt.Format(time.RFC3339),
		})
	}

	if err := rows.Err(); err != nil {
		log.Fatal("Row iteration error:", err)
	}
}

func nullableString(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

func byteSliceToString(b *[]byte) string {
	if b == nil {
		return ""
	}
	return string(*b)
}
