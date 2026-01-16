import streamlit as st


def setup_page():
    # Set page config
    st.set_page_config(
        page_title="🔬 Research RAG",
        layout="centered",
        initial_sidebar_state="expanded",
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
