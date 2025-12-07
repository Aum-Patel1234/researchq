"""
Helper functions for Streamlit UI rendering of RAG responses.
"""

import streamlit as st
from typing import Any


def extract_answer_from_result(result: Any) -> str:
    """
    Extract the answer text from a RAG result.
    
    Parameters
    ----------
    result : Any
        The result from graph_builder.run(), can be RAGState object or dict.
    
    Returns
    -------
    str
        The answer text, or empty string if not found.
    """
    # Try to get answer from RAGState object (Pydantic model)
    if hasattr(result, "answer"):
        answer = getattr(result, "answer", None)
        if answer:
            return answer if isinstance(answer, str) else str(answer)
    
    # Try dictionary representation
    if isinstance(result, dict):
        answer = result.get("answer", "")
        if answer:
            return answer if isinstance(answer, str) else str(answer)
    
    # If result is a Pydantic model, try model_dump() or dict() method
    if hasattr(result, "model_dump"):
        try:
            result_dict = result.model_dump()
            answer = result_dict.get("answer", "")
            if answer:
                return answer if isinstance(answer, str) else str(answer)
        except Exception:
            pass
    
    if hasattr(result, "dict"):
        try:
            result_dict = result.dict()
            answer = result_dict.get("answer", "")
            if answer:
                return answer if isinstance(answer, str) else str(answer)
        except Exception:
            pass
    
    # Fallback: return empty string instead of string representation of whole object
    return ""


def render_answer(answer_text: str):
    """
    Render the answer text properly formatted in Streamlit.
    
    This function handles markdown formatting, including:
    - Headings and subheadings
    - Lists (ordered and unordered)
    - Code blocks
    - Bold/italic text
    - Paragraphs
    
    Parameters
    ----------
    answer_text : str
        The answer text to render (typically in markdown format).
    """
    if not answer_text:
        st.warning("No answer generated.")
        return
    
    # Render as markdown to preserve formatting
    st.markdown(answer_text, unsafe_allow_html=False)


def display_rag_result(result: Any):
    """
    Display a RAG result properly formatted in Streamlit.
    
    Parameters
    ----------
    result : Any
        The result from graph_builder.run(), can be RAGState object or dict.
    """
    answer_text = extract_answer_from_result(result)
    render_answer(answer_text)

