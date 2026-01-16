from logging import Logger
import streamlit as st
from typing import List, Any
import traceback


def process_documents(docs: List[Any], processor, logger: Logger) -> List[Any]:
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
