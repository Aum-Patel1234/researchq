# Integration Guide: FAISS + Embedding Server + PostgreSQL

This guide explains how the system integrates the FAISS index, embedding server API, and PostgreSQL database.

## Architecture Overview

1. **FAISS Index**: Pre-built vector index at `embedding_engine/build/paper.faiss`
2. **Embedding Server**: FastAPI server that generates embeddings for queries (BGE model)
3. **PostgreSQL Database**: Stores chunks and metadata (paper titles, authors, etc.)

## Setup

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Embedding Server
EMBEDDING_SERVER_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/final_year_rag

# FAISS Index Path (relative to project root)
FAISS_INDEX_PATH=embedding_engine/build/paper.faiss

# LLM Configuration
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `psycopg2-binary` - PostgreSQL adapter
- `faiss-cpu` - FAISS vector search (already present)
- `requests` - HTTP client (already present)

### 3. Start Embedding Server

Make sure the embedding server is running:

```bash
cd embedding_server
uvicorn main:app --reload --port 8000
```

### 4. Verify Database Connection

Ensure PostgreSQL is running and contains:
- `embedding_chunks` table with chunks
- `research_papers` table with paper metadata
- FAISS IDs in `embedding_chunks.id` match the FAISS index IDs

## How It Works

### Query Flow

1. **User asks a question** in Streamlit UI
2. **Get query embedding**: Query is sent to embedding server API (`/embed` endpoint)
3. **Search FAISS**: Query vector is searched against pre-built FAISS index
4. **Fetch chunks**: Top-k chunk IDs from FAISS are used to fetch chunks and metadata from PostgreSQL
5. **Display results**: Chunks are displayed with metadata (paper title, authors, etc.)
6. **Generate answer**: LLM generates answer using retrieved chunks as context

### VectorStore Class

The new `FAISSVectorStore` class in `src/vectorstore/vectorstore.py`:
- Loads FAISS index on initialization
- Connects to PostgreSQL database
- Implements LangChain retriever interface
- Prints vectors and chunks to console for debugging

### Database Schema

The system expects these tables:

**embedding_chunks**:
- `id` (BIGSERIAL) - Primary key, also used as FAISS ID
- `document_id` (BIGINT) - Foreign key to research_papers
- `chunk_index` (INT) - Position in document
- `page_number` (INT) - Page number
- `chunk_text` (TEXT) - The actual chunk text
- `embedding_model` (TEXT) - Model used for embedding

**research_papers**:
- `id` (BIGSERIAL) - Primary key
- `title` (TEXT) - Paper title
- `authors` (TEXT) - Authors
- `doi` (TEXT) - DOI
- `source` (TEXT) - Source URL

## Usage

1. Start the embedding server
2. Run Streamlit app: `streamlit run streamlit_app.py`
3. Click "Initialize Vector Store" in the sidebar
4. Enter a question and get answers!

## Debugging

The system prints detailed information to console:
- Query vectors (shape, first values, norm)
- FAISS search results (scores, IDs)
- Stored vectors from FAISS index
- Chunk details (text, metadata, scores)

Enable debug mode in Streamlit sidebar for additional information.

## Troubleshooting

### FAISS Index Not Found
- Check that `paper.faiss` exists at the specified path
- Verify `FAISS_INDEX_PATH` in `.env` is correct

### Database Connection Error
- Verify PostgreSQL is running
- Check `DATABASE_URL` format: `postgresql://user:password@host:port/database`
- Ensure database contains required tables

### Embedding Server Error
- Verify server is running on the specified port
- Check `EMBEDDING_SERVER_URL` in `.env`
- Test with: `curl http://localhost:8000/health`

### Dimension Mismatch
- FAISS index dimension must match embedding dimension (default: 768)
- Check embedding server model output dimension

