import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
from typing import List

MODEL_NAME = "BAAI/bge-base-en-v1.5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ------------------ Load model ------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.to(DEVICE)
model.eval()

# ------------------ FastAPI ------------------
app = FastAPI(title="BGE Embedding Server")


class EmbeddingRequest(BaseModel):
    texts: List[str]
    is_query: bool = False  # True for query, False for documents


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9
    )


@torch.no_grad()
def embed(texts: List[str], is_query: bool):
    if is_query:
        texts = [
            f"Represent this sentence for searching relevant passages: {t}"
            for t in texts
        ]

    encoded = tokenizer(
        texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
    ).to(DEVICE)

    output = model(**encoded)
    embeddings = mean_pooling(output, encoded["attention_mask"])

    # Normalize (VERY IMPORTANT)
    embeddings = torch.nn.functional.normalize(embeddings)

    return embeddings.cpu().numpy().astype("float32")


@app.post("/embed")
def create_embeddings(req: EmbeddingRequest):
    vectors = embed(req.texts, req.is_query)
    return {"dim": vectors.shape[1], "embeddings": vectors.tolist()}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": DEVICE}
