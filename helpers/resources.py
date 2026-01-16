import streamlit as st
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FAISS_INDEX_PATH = PROJECT_ROOT / "embedding_engine" / "build" / "paper.faiss"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/final_year_rag"


def create_resource_getters(components, logger, FAISSVectorStoreClass):
    """
    Factory function to avoid global state & circular imports.
    Returns cached resource getter functions.
    """

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
            faiss_path = getattr(config, "FAISS_INDEX_PATH", FAISS_INDEX_PATH)

            faiss_path_obj = Path(faiss_path)
            if not faiss_path_obj.is_absolute():
                faiss_path = PROJECT_ROOT / faiss_path

            if not faiss_path.exists():
                raise FileNotFoundError(
                    f"FAISS index not found at {faiss_path}. "
                    "Expected: embedding_engine/build/paper.faiss"
                )

            embedding_server_url = getattr(
                config, "EMBEDDING_SERVER_URL", "http://localhost:8000"
            )
            database_url = getattr(
                config,
                "DATABASE_URL",
                DATABASE_URL,
            )

            logger.info("Initializing FAISSVectorStore")
            logger.info(f"FAISS path: {faiss_path}")
            logger.info(f"Embedding server: {embedding_server_url}")
            # logger.info(f"Database: {database_url[:30]}...")  # Don't log full password

            return FAISSVectorStoreClass(
                faiss_index_path=faiss_path,
                embedding_server_url=embedding_server_url,
                database_url=database_url,
            )
        except Exception as e:
            logger.error(f"Error initializing FAISSVectorStore: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    return get_document_processor, get_llm, get_vector_store
