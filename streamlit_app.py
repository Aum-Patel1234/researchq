"""
streamlit_app.py
Robust Streamlit UI for Agentic RAG System

This version includes:
- Better error handling and logging
- Improved UI/UX
- Debug mode for troubleshooting
- Proper initialization of components
- Clear error messages
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
import os
import logging
from typing import List, Any
import traceback


from src.config.config import Config as ConfigClass
from src.document_ingestion.document_processor import (
    DocumentProcessor as DocumentProcessorClass,
)

from src.vectorstore.vectorstore import (
    VectorStore as VectorStoreClass,
    FAISSVectorStore as FAISSVectorStoreClass,
)
from src.graph_builder.graph_builder import GraphBuilder as GraphBuilderClass
from src.state.rag_state import RAGState as RAGStateClass
from src.streamlithelper import display_rag_result, extract_answer_from_result


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Add project root to path (so src imports work correctly)
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set page config
st.set_page_config(
    page_title="🔬 Research RAG", layout="centered", initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown(
    """
    <style>
    .stButton > button {
        width: 100%; 
        font-weight: 600;
        margin: 0.5rem 0;
    }
    .stTextInput, .stTextArea { 
        width: 100%; 
    }
    .debug-info {
        font-family: monospace;
        font-size: 0.8em;
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .error-message {
        color: #ff4b4b;
        font-weight: bold;
    }
    .success-message {
        color: #00c853;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# -------------------------
# Initialize components with error handling
# -------------------------
def init_components():
    """Initialize all required components with error handling."""
    components: dict[str, type] = {
        "Config": ConfigClass,
        "DocumentProcessor": DocumentProcessorClass,
        "VectorStore": VectorStoreClass,
        "GraphBuilder": GraphBuilderClass,
        "RAGState": RAGStateClass,
    }

    # Import Config
    try:
        components["Config"] = ConfigClass
        logger.info("Successfully imported Config")
    except ImportError as e:
        logger.error(f"Failed to import Config: {str(e)}")
        st.error("❌ Failed to import configuration. Please check config.py")

    # Import DocumentProcessor
    try:
        components["DocumentProcessor"] = DocumentProcessorClass
        logger.info("Successfully imported DocumentProcessor")
    except ImportError as e:
        logger.error(f"Failed to import DocumentProcessor: {str(e)}")
        st.error("❌ Failed to import DocumentProcessor. Check document_ingestion/")

    # Import VectorStore
    try:
        components["VectorStore"] = VectorStoreClass
        logger.info("Successfully imported VectorStore")
    except ImportError as e:
        logger.error(f"Failed to import VectorStore: {str(e)}")
        st.error("❌ Failed to import VectorStore. Check vectorstore/")

    # Import GraphBuilder and RAGState
    try:
        components["GraphBuilder"] = GraphBuilderClass
        components["RAGState"] = RAGStateClass
        logger.info("Successfully imported GraphBuilder and RAGState")
    except ImportError as e:
        logger.error(f"Failed to import GraphBuilder/RAGState: {str(e)}")
        st.error(
            "❌ Failed to import GraphBuilder or RAGState. Check graph_builder/ and state/"
        )

    return components


# Initialize components
components = init_components()


# -------------------------
# Cached resources with error handling
# -------------------------
@st.cache_resource(show_spinner=False)
def get_document_processor():
    """Initialize and return DocumentProcessor with error handling."""
    if not components["DocumentProcessor"]:
        raise ImportError(
            "DocumentProcessor not available. Check the logs for details."
        )

    try:
        # Get chunking parameters from Config if available
        chunk_size = 500
        chunk_overlap = 50

        if components["Config"]:
            chunk_size = getattr(components["Config"], "CHUNK_SIZE", chunk_size)
            chunk_overlap = getattr(
                components["Config"], "CHUNK_OVERLAP", chunk_overlap
            )

        logger.info(
            f"Initializing DocumentProcessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )
        return components["DocumentProcessor"](
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    except Exception as e:
        logger.error(f"Error initializing DocumentProcessor: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


@st.cache_resource(show_spinner=False)
def get_llm():
    """Initialize and return the LLM with error handling."""
    if not components["Config"]:
        raise ImportError("Config not available. Check the logs for details.")

    try:
        logger.info("Initializing LLM...")
        config = components["Config"]

        # Try different ways to get the LLM
        if hasattr(config, "get_llm") and callable(config.get_llm):
            logger.info("Using Config.get_llm()")
            return config.get_llm()
        elif hasattr(config, "LLM"):
            logger.info("Using Config.LLM")
            return config.LLM
        elif hasattr(config, "llm"):
            logger.info("Using config.llm")
            return config.llm
        else:
            raise AttributeError("No valid LLM configuration found in Config")
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


@st.cache_resource(show_spinner=False)
def get_vector_store():
    """Initialize and return FAISSVectorStore with error handling."""
    if not components["Config"]:
        raise ImportError("Config not available. Check the logs for details.")

    try:
        config = components["Config"]
        # Get FAISS path and resolve it relative to project root
        faiss_path = getattr(
            config, "FAISS_INDEX_PATH", "embedding_engine/build/paper.faiss"
        )
        # Resolve to absolute path if relative
        from pathlib import Path

        faiss_path_obj = Path(faiss_path)
        if not faiss_path_obj.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent
            faiss_path = str(project_root / faiss_path)

        embedding_server_url = getattr(
            config, "EMBEDDING_SERVER_URL", "http://localhost:8000"
        )
        database_url = getattr(
            config,
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/final_year_rag",
        )

        logger.info("Initializing FAISSVectorStore")
        logger.info(f"FAISS path: {faiss_path}")
        logger.info(f"Embedding server: {embedding_server_url}")
        logger.info(f"Database: {database_url[:30]}...")  # Don't log full password

        return FAISSVectorStoreClass(
            faiss_index_path=faiss_path,
            embedding_server_url=embedding_server_url,
            database_url=database_url,
            embedding_dim=768,  # BGE models typically use 768
        )
    except Exception as e:
        logger.error(f"Error initializing FAISSVectorStore: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


# -------------------------
# Helper functions
# -------------------------
def save_uploaded_file(uploaded_file) -> Path:
    """Save uploaded file to a temporary location."""
    try:
        suffix = Path(uploaded_file.name).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            logger.info(f"Saved uploaded file to {tmp.name}")
            return Path(tmp.name)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


def process_documents(docs: List[Any], processor) -> List[Any]:
    """Process documents with error handling."""
    try:
        logger.info(f"Processing {len(docs)} documents")
        processed_docs = []
        for doc in docs:
            if hasattr(processor, "process_document"):
                processed_docs.append(processor.process_document(doc))
            else:
                processed_docs.append(doc)
        return processed_docs
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


def display_document_info(docs: List[Any]):
    """Display information about the processed documents."""
    if not docs:
        st.warning("No documents to display.")
        return

    st.subheader("📄 Processed Documents")
    for i, doc in enumerate(docs, 1):
        with st.expander(f"Document {i} (Click to expand)"):
            st.json(
                {
                    "Page Content": (
                        doc.page_content[:500] + "..."
                        if len(doc.page_content) > 500
                        else doc.page_content
                    ),
                    "Metadata": doc.metadata,
                }
            )


# -------------------------
# Main UI
# -------------------------
def main():
    st.title("🔬 Research Paper RAG System")
    st.markdown("Upload research papers or enter URLs to ask questions about them.")

    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)
    if debug_mode:
        st.sidebar.subheader("Debug Information")
        st.sidebar.json(
            {
                "Python Version": sys.version,
                "Working Directory": os.getcwd(),
                "System Path": sys.path,
            }
        )

    # Initialize session state
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "retriever" not in st.session_state:
        st.session_state.retriever = None

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info("Using pre-built FAISS index and PostgreSQL database")

        # Initialize vector store button
        init_btn = st.button("Initialize Vector Store", type="primary")

        if init_btn or st.session_state.vector_store is None:
            with st.spinner("Initializing vector store..."):
                try:
                    vector_store = get_vector_store()
                    st.session_state.vector_store = vector_store
                    st.session_state.retriever = vector_store.get_retriever()
                    st.success("✅ Vector store initialized successfully!")
                    if debug_mode:
                        st.json(
                            {
                                "FAISS Index": f"{vector_store.index.ntotal} vectors",
                                "Embedding Dimension": vector_store.embedding_dim,
                                "Embedding Server": vector_store.embedding_server_url,
                            }
                        )
                except Exception as e:
                    st.error(f"Failed to initialize vector store: {str(e)}")
                    logger.error(f"Vector store initialization error: {str(e)}")
                    logger.debug(traceback.format_exc())

    # Question input
    st.divider()
    st.subheader("❓ Ask a Question")
    question = st.text_input("Enter your question about the research papers")

    if question and st.session_state.retriever:
        with st.spinner("Searching for answers..."):
            try:
                # Get relevant documents (retriever.invoke returns list of documents)
                relevant_docs = st.session_state.retriever.invoke(question)

                # Display vectors and chunks information
                st.subheader("🔍 Retrieved Vectors & Chunks")
                st.info(f"Found {len(relevant_docs)} relevant chunks")

                # Print vectors and chunks info
                for i, doc in enumerate(relevant_docs, 1):
                    with st.expander(
                        f"Chunk {i} - Score: {doc.metadata.get('similarity_score', 'N/A'):.4f}"
                    ):
                        st.write("**Chunk Text:**")
                        st.write(doc.page_content)
                        st.write("**Metadata:**")
                        st.json(
                            {
                                "Chunk ID": doc.metadata.get("chunk_id"),
                                "Document ID": doc.metadata.get("document_id"),
                                "Paper Title": doc.metadata.get("paper_title"),
                                "Authors": doc.metadata.get("authors"),
                                "DOI": doc.metadata.get("doi"),
                                "Source": doc.metadata.get("source"),
                                "Page Number": doc.metadata.get("page_number"),
                                "Chunk Index": doc.metadata.get("chunk_index"),
                                "Similarity Score": doc.metadata.get(
                                    "similarity_score"
                                ),
                            }
                        )

                        # Print to console/logs
                        logger.info(f"\n{'='*60}")
                        logger.info(f"CHUNK {i}")
                        logger.info(f"{'='*60}")
                        logger.info(f"Chunk ID: {doc.metadata.get('chunk_id')}")
                        logger.info(
                            f"Similarity Score: {doc.metadata.get('similarity_score')}"
                        )
                        logger.info(f"Paper: {doc.metadata.get('paper_title')}")
                        logger.info(f"Authors: {doc.metadata.get('authors')}")
                        logger.info(
                            f"Chunk Text (first 300 chars): {doc.page_content[:300]}..."
                        )
                        logger.info(f"Full Chunk Text:\n{doc.page_content}")

                # Display relevant documents summary
                st.subheader("📚 Relevant Context Summary")
                for i, doc in enumerate(relevant_docs[:5], 1):  # Show top 5
                    st.write(
                        f"**{i}. {doc.metadata.get('paper_title', 'Unknown Paper')}**"
                    )
                    st.caption(
                        f"Authors: {doc.metadata.get('authors', 'Unknown')} | Score: {doc.metadata.get('similarity_score', 0):.4f}"
                    )
                    st.write(
                        doc.page_content[:300] + "..."
                        if len(doc.page_content) > 300
                        else doc.page_content
                    )
                    st.divider()

                # Generate answer using LLM and GraphBuilder
                llm = get_llm()

                # Initialize graph builder
                graph_builder = components["GraphBuilder"](
                    retriever=st.session_state.retriever, llm=llm
                )

                # Run the graph
                result = graph_builder.run(question)

                # Display answer (result is RAGState object)
                st.subheader("💡 Answer")
                display_rag_result(result)

                # Debug info
                if debug_mode:
                    answer_text = extract_answer_from_result(result)
                    st.subheader("🔍 Debug Information")
                    st.json(
                        {
                            "Question": question,
                            "Retrieved Documents": len(relevant_docs),
                            "Answer Length": len(answer_text) if answer_text else 0,
                            "Result Type": type(result).__name__,
                            "Has Answer Attribute": hasattr(result, "answer"),
                        }
                    )

            except Exception as e:
                st.error(f"An error occurred while generating an answer: {str(e)}")
                logger.error(f"Answer generation error: {str(e)}")
                logger.debug(traceback.format_exc())
    elif question:
        st.warning("Please initialize the vector store first using the sidebar.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        st.error("A critical error occurred. Please check the logs for more details.")
