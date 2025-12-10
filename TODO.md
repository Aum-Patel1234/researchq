IMP - there are 4 of use each Pinecone db for exactly one subject like 1 for nlp...

1. Make a script for loading docs to Pinecone db.
   - make a script to run on cloud

2. Set up GPU for the embedding model.
   - make a python script and expose it to my backend

3. deploy on cloud and make whole ci/cd

# 📝 TODO for Data Ingestion

## 1️⃣ Go Ingestion Pipeline

* [ ] Implement Arxiv fetcher (`internal/arxiv/arxiv.go`)
* [ ] Implement Semantic Scholar fetcher (`internal/arxiv/semantic.go`)
* [ ] Implement Springer Nature fetcher (`internal/arxiv/springer.go`)
* [ ] Implement embedding generator (`internal/embedding/embedding.go`)
* [ ] Implement Pinecone uploader (`internal/pinecone/pinecone.go`)
* [ ] Implement pipeline orchestrator (`internal/pipeline/pipeline.go`)
* [ ] Add logging to track ingestion progress (`internal/logger/logger.go`)
* [ ] Handle deduplication based on `title` in Postgres

## 3️⃣ Log Server (HTTP Endpoint)

* [ ] Create small HTTP server to serve logs (`/logs`)
* [ ] Optional: add live streaming or filtering (`?source=arxiv`)
* [ ] Integrate log rotation (`lumberjack.Logger`)

## 4️⃣ Background Process / EC2

* [ ] Deploy ingestion pipeline to EC2
* [ ] Configure as background service / systemd service
* [ ] Ensure logs are written and accessible via HTTP server

## 5️⃣ CI / CD

* [ ] Add GitHub workflow for Go build and tests
* [ ] Optional: Dockerize the ingestion app
* [ ] Push Docker image for deployment

## 6️⃣ Testing / Debugging

* [ ] Test fetching from each API separately
* [ ] Test embeddings + Pinecone upload
* [ ] Test Postgres insertions and deduplication
* [ ] Monitor logs via HTTP endpoint

## 7️⃣ Documentation

* [ ] Update `README.md` with project structure, instructions
* [ ] Document `.env` variables and setup
* [ ] Document Makefile targets
