# BGE Embedding Server (FastAPI)

This server provides embeddings using `BAAI/bge-base-en-v1.5` and returns JSON responses compatible with your C++ client's existing parser (Gemini-like):

```json
{
  "responses": [
    {"embedding": {"values": [0.01, -0.02, ...]}},
    ...
  ]
}
```

```bash
pip install -r requirements.txt
```
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```