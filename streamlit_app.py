"""
streamlit_app.py
Streamlit UI for Agentic RAG System (matches your project layout)

Features:
- Uses Config.get_llm(), DocumentProcessor, VectorStore, GraphBuilder from src/
- Ingest DEFAULT_URLS or upload PDF files
- Build FAISS index & Graph
- Ask questions and display long answers + retrieved chunks
"""

import streamlit as st
from pathlib import Path
import sys
import time
import tempfile
import os
from typing import List

# Ensure src is importable (adjust if your package layout differs)
sys.path.append(str(Path(__file__).parent / "src"))

from config.config import Config  # relative to src/config/config.py
from document_ingestion.document_processor import DocumentProcessor
from vectorstore.vectorstore import VectorStore
from graph_builder.graph_builder import GraphBuilder
from langchain_core.documents import Document as LcDocument

st.set_page_config(page_title="🔬 Research RAG", layout="centered")

st.markdown(
    """
    <style>
    .stButton > button { width: 100%; font-weight: 600; }
    .stTextInput, .stTextArea { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Helpers / Cached resources
# -------------------------
@st.cache_resource(show_spinner=False)
def init_processor() -> DocumentProcessor:
    return DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE, chunk_overlap=Config.CHUNK_OVERLAP
    )


@st.cache_resource(show_spinner=False)
def init_llm():
    """Return the LLM instance from Config."""
    return Config.get_llm()


@st.cache_resource(show_spinner=False)
def init_vector_store(embedding_model: str):
    """Return an empty VectorStore instance (with embedding model)."""
    return VectorStore(embedding_model)


def save_uploaded_file(uploaded) -> Path:
    suffix = Path(uploaded.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        return Path(tmp.name)


def normalize_result(result):
    """
    Normalize graph result to dict with keys: answer (str), retrieved_docs (List[Document])
    Accepts dict-like or object-like results.
    """
    if result is None:
        return {"answer": None, "retrieved_docs": []}

    # dict-like
    if isinstance(result, dict):
        answer = (
            result.get("answer") or result.get("output") or result.get("result") or None
        )
        docs = (
            result.get("retrieved_docs")
            or result.get("retrieved")
            or result.get("docs")
            or []
        )
        return {"answer": answer, "retrieved_docs": docs}

    # object-like (RAGState)
    answer = getattr(result, "answer", None)
    docs = getattr(result, "retrieved_docs", []) or getattr(result, "retrieved", [])
    # if docs are stored in attribute 'documents'
    if not docs:
        docs = getattr(result, "documents", [])
    return {"answer": answer, "retrieved_docs": docs}


def ensure_node_name_compat(graph_builder: GraphBuilder):
    """
    GraphBuilder.build() in your repo expects a node method name 'generate_anser' (typo),
    while some node implementations use 'generate_answer'. Patch the node object if needed.
    """
    nodes = getattr(graph_builder, "nodes", None)
    if not nodes:
        return
    # if nodes has generate_answer but not generate_anser, alias it
    if hasattr(nodes, "generate_answer") and not hasattr(nodes, "generate_anser"):
        setattr(nodes, "generate_anser", getattr(nodes, "generate_answer"))


# -------------------------
# UI / Main
# -------------------------
def main():
    st.title("🔬 Research Paper RAG — Assistant")
    st.write(
        "Ingest PDFs (upload or URL), build index, then ask long research-style questions."
    )

    # Initialize session state
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "graph_builder" not in st.session_state:
        st.session_state.graph_builder = None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "last_documents" not in st.session_state:
        st.session_state.last_documents = []

    processor = init_processor()

    st.sidebar.header("Initialization")
    if st.sidebar.button("Initialize system (load DEFAULT_URLS)"):
        with st.spinner("Loading default documents and building index..."):
            try:
                llm = init_llm()
                # ingest default URLs
                urls = getattr(Config, "DEFAULT_URLS", [])
                docs_all: List[LcDocument] = []
                for u in urls:
                    # try to load as PDF first, fall back to web page loader
                    try:
                        docs = processor.load_pdf_from_url(u)
                    except Exception:
                        docs = processor.load_from_url(u)
                    # chunk if needed
                    docs_all.extend(processor.split_documents(docs))

                st.session_state.last_documents = docs_all

                # create vectorstore
                vs = init_vector_store(Config.EMBEDDING_MODEL)
                vs.create_retriever(st.session_state.last_documents)
                st.session_state.vector_store = vs

                # build graph
                gb = GraphBuilder(retriever=vs.get_retriever(), llm=llm)
                # patch node name mismatches if necessary
                ensure_node_name_compat(gb)
                gb.build()
                st.session_state.graph_builder = gb
                st.session_state.initialized = True
                st.success(f"Initialized. Loaded {len(docs_all)} chunks.")
            except Exception as e:
                st.exception(f"Initialization failed: {e}")

    st.sidebar.markdown("---")
    st.sidebar.header("Manual ingestion")
    uploaded = st.sidebar.file_uploader(
        "Upload PDF(s)", type=["pdf"], accept_multiple_files=True
    )
    pdf_url = st.sidebar.text_input("Or paste a direct PDF URL")

    if st.sidebar.button("Ingest now"):
        with st.spinner("Ingesting files/URL..."):
            docs_all: List[LcDocument] = st.session_state.get("last_documents", [])
            # upload files
            if uploaded:
                for f in uploaded:
                    try:
                        path = save_uploaded_file(f)
                        docs = processor.load_from_pdf(str(path))
                        docs_all.extend(processor.split_documents(docs))
                        os.remove(path)
                    except Exception as e:
                        st.error(f"Failed to process {f.name}: {e}")
            # pdf url
            if pdf_url:
                try:
                    docs = processor.load_pdf_from_url(pdf_url)
                    docs_all.extend(processor.split_documents(docs))
                except Exception as e:
                    st.error(f"Failed to download/load PDF: {e}")

            if docs_all:
                st.session_state.last_documents = docs_all
                # (re)create vectorstore
                try:
                    vs = init_vector_store(Config.EMBEDDING_MODEL)
                    vs.create_retriever(docs_all)
                    st.session_state.vector_store = vs
                    st.success(f"Ingested and indexed {len(docs_all)} chunks.")
                except Exception as e:
                    st.exception(f"Failed to build vectorstore: {e}")
            else:
                st.info("No documents ingested.")

    st.markdown("---")

    # Query area
    st.header("Ask a question about loaded papers")
    question = st.text_area(
        "Question",
        height=120,
        placeholder="Ask about methods, equations, comparisons, etc.",
    )
    cols = st.columns([1, 1, 1])
    temp = cols[0].slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    top_k = cols[1].number_input(
        "Top-k chunks", min_value=1, max_value=20, value=6, step=1
    )
    run_btn = cols[2].button("Get Answer")

    if run_btn:
        if not st.session_state.initialized or st.session_state.graph_builder is None:
            st.error(
                "System not initialized. Initialize first (sidebar) or ingest documents."
            )
        elif not question.strip():
            st.error("Please enter a question.")
        else:
            gb: GraphBuilder = st.session_state.graph_builder
            # Ensure nodes compatibility (in case graph_builder was created before patch)
            ensure_node_name_compat(gb)

            with st.spinner("Running RAG graph..."):
                start = time.time()
                try:
                    raw = gb.run(question)  # may return dict or RAGState-like object
                except Exception as e:
                    st.exception(f"Graph execution failed: {e}")
                    raw = None
                elapsed = time.time() - start

            normalized = normalize_result(raw)
            answer = normalized["answer"] or "No answer generated."
            docs = normalized["retrieved_docs"] or []

            st.markdown("### Answer")
            st.success(answer)

            st.markdown("### Retrieved Chunks (top-k)")
            for i, d in enumerate(docs[:top_k], start=1):
                meta = getattr(d, "metadata", {}) or {}
                title = meta.get("title") or meta.get("source") or f"doc_{i}"
                st.markdown(f"**[{i}] {title}**")
                st.text_area(
                    f"Chunk {i}", value=d.page_content[:2000], height=120, disabled=True
                )

            st.caption(f"Response time: {elapsed:.2f}s")

    # history & simple status
    st.markdown("---")
    st.subheader("Status")
    st.write(f"Initialized: {st.session_state.initialized}")
    st.write(f"Indexed chunks: {len(st.session_state.get('last_documents', []))}")


if __name__ == "__main__":
    main()
