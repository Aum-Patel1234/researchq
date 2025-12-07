# 🚀 researchq – RAG Based Research Question Assistant

This project uses **LangChain**, **FAISS**, **Streamlit**, and **UV** to process research PDFs and query them using RAG (Retrieval-Augmented Generation).

🟢 Works on Linux / Ubuntu / AWS EC2  
🐳 Fully Dockerized build & run  
⚡ No manual environment setup required — just `docker build` & `docker run`

---

## 📦 Prerequisites

Ensure you have:

| Requirement | Version |
|------------|----------|
| Docker | ≥ 20.x |
| Git (for cloning repo) | any |

---

## Environment Variables

```bash
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"

GOOGLE_API_KEY=""
GEMINI_MODEL=""

PDF_DATA_DIR="./data"

FAISS_INDEX_PATH="./vectorstore/index.faiss"
FAISS_STORE_PATH="./vectorstore/store.pkl"

APP_ENV="production"   # development | production
LOG_LEVEL="info"       # debug | info | warning | error

USER_AGENT="final_year_rag_app/1.0"
```

---

## 🐳 Build & Run with Docker

```bash
git clone https://github.com/Aum-Patel1234/researchq.git
cd researchq

# build image
docker build -t researchq:latest .

# run container on port 8501
docker run --rm -it -p 8501:8501 researchq:latest
```

Now open in browser:

```
http://localhost:8501
```

---

## 🚀 Deploy on AWS EC2 (Ubuntu/Linux)

```bash
sudo apt update && sudo apt install -y docker.io
sudo systemctl enable docker --now

git clone https://github.com/Aum-Patel1234/researchq.git
cd researchq

docker build -t researchq:latest .
docker run -d -p 8501:8501 researchq:latest
```

Access the app via **EC2 Public IPv4**:

```
http://YOUR_EC2_PUBLIC_IP:8501
```

Keep container alive even if terminal closes:

```bash
docker run -d --restart always -p 8501:8501 researchq:latest
```

---

## 🛠 Tech Stack

| Component | Used For |
|----------|-----------|
| UV | Fast Python Environment Mgmt |
| Streamlit | UI |
| LangChain | RAG Pipeline |
| FAISS | Vector Store |
| GEMINI | LLM Backend |

---

## 🧠 Future Enhancements

- Support Multiple Vector Stores
- Advanced Chunking Methods
- Document Summaries + Agents