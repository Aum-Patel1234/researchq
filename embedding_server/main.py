#!/usr/bin/env python3
# main.py - BGE embedding server that returns Gemini-like JSON "responses" array
import os
import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from transformers import AutoTokenizer, AutoModel
from time import time

# Config
MODEL_NAME = os.environ.get("BGE_MODEL", "BAAI/bge-base-en-v1.5")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_BATCH = int(os.environ.get("BATCH_MAX", "128"))
MAX_LENGTH = int(os.environ.get("MAX_TOKENS", "512"))

# Load tokenizer + model once at startup
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.to(DEVICE)
model.eval()

app = FastAPI(title="BGE Embedding Server")


# Request model: list of chunk texts. Keep simple and compatible with your pipeline.
class EmbedRequest(BaseModel):
    texts: List[str]
    is_query: Optional[bool] = False


# Helper pooling function (mean pooling ignoring padding)
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state  # (B, T, D)
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = torch.sum(token_embeddings * mask, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts


@torch.no_grad()
def compute_embeddings(texts: List[str], is_query: bool) -> np.ndarray:
    # Optionally prefix queries to match BGE training
    if is_query:
        texts = [
            f"Represent this sentence for searching relevant passages: {t}"
            for t in texts
        ]

    # Tokenize and move to device
    encoded = tokenizer(
        texts, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt"
    ).to(DEVICE)

    outputs = model(**encoded)
    embeddings = mean_pooling(outputs, encoded["attention_mask"])  # (B, D)

    # L2-normalize for cosine similarity (so dot product == cosine)
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    # Move to CPU float32 numpy
    return embeddings.cpu().numpy().astype("float32")


# API: /embed - returns JSON like: { "responses": [ { "embedding": { "values": [..] } } ] }
@app.post("/embed")
def embed(req: EmbedRequest):
    texts = req.texts
    if not texts:
        raise HTTPException(
            status_code=400, detail="`texts` must be a non-empty list of strings"
        )
    if len(texts) > MAX_BATCH:
        raise HTTPException(status_code=413, detail=f"Batch too large. Max {MAX_BATCH}")

    t0 = time()
    vectors = compute_embeddings(texts, bool(req.is_query))
    latency = time() - t0

    # Build Gemini-like response shape
    responses = []
    for vec in vectors:
        # convert numpy float32 array to native python list of floats
        responses.append({"embedding": {"values": vec.tolist()}})

    return {
        "model": MODEL_NAME,
        "device": DEVICE,
        "batch_size": len(texts),
        "dim": vectors.shape[1],
        "latency_sec": latency,
        "responses": responses,
    }


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": DEVICE}
