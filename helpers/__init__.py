import streamlit as st
from src.vectorstore.vectorstore import (
    VectorStore as VectorStoreClass,
)
from src.graph_builder.graph_builder import GraphBuilder as GraphBuilderClass
from src.state.rag_state import RAGState as RAGStateClass
from src.config.config import Config as ConfigClass
from src.document_ingestion.document_processor import (
    DocumentProcessor as DocumentProcessorClass,
)

import logging


# -------------------------
# Initialize components with error handling
# -------------------------
def init_components(logger: logging.Logger) -> dict[str, type]:
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
        st.error("Failed to import configuration. Please check config.py")

    # Import DocumentProcessor
    try:
        components["DocumentProcessor"] = DocumentProcessorClass
        logger.info("Successfully imported DocumentProcessor")
    except ImportError as e:
        logger.error(f"Failed to import DocumentProcessor: {str(e)}")
        st.error("Failed to import DocumentProcessor. Check document_ingestion/")

    # Import VectorStore
    try:
        components["VectorStore"] = VectorStoreClass
        logger.info("Successfully imported VectorStore")
    except ImportError as e:
        logger.error(f"Failed to import VectorStore: {str(e)}")
        st.error("Failed to import VectorStore. Check vectorstore/")

    # Import GraphBuilder and RAGState
    try:
        components["GraphBuilder"] = GraphBuilderClass
        components["RAGState"] = RAGStateClass
        logger.info("Successfully imported GraphBuilder and RAGState")
    except ImportError as e:
        logger.error(f"Failed to import GraphBuilder/RAGState: {str(e)}")
        st.error(
            "Failed to import GraphBuilder or RAGState. Check graph_builder/ and state/"
        )

    return components
