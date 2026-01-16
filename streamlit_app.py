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

import sys
import streamlit as st
import os
import logging
import traceback

from helpers import init_components
from src.vectorstore.vectorstore import (
    FAISSVectorStore as FAISSVectorStoreClass,
)
from helpers.resources import create_resource_getters
from helpers.streamlit_render import display_rag_result, extract_answer_from_result
from helpers.ui import setup_page

# # Add project root to path (so src imports work correctly)
# PROJECT_ROOT = Path(__file__).parent
# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# setup basic layout of page
setup_page()

# Initialize components
components = init_components(logger)

# get resource helper funcs
get_document_processor, get_llm, get_vector_store = create_resource_getters(
    components, logging, FAISSVectorStoreClass
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
