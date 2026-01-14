import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class Config:
    """
    Central configuration class for the Research RAG pipeline.
    Loads environment variables and exposes helper methods to
    initialize the embedding model and the Gemini LLM.
    """

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
    )
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # Embedding server configuration
    EMBEDDING_SERVER_URL = os.getenv("EMBEDDING_SERVER_URL", "http://localhost:8000")

    # Database configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/final_year_rag"
    )

    # FAISS index path
    FAISS_INDEX_PATH = os.getenv(
        "FAISS_INDEX_PATH", "embedding_engine/build/paper.faiss"
    )

    DEFAULT_URLS = [
        # Attention Is All You Need (Transformer)
        "https://arxiv.org/pdf/1706.03762.pdf",
        # # BERT: Pre-training of Deep Bidirectional Transformers
        # "https://arxiv.org/pdf/1810.04805.pdf",
        # # GPT-3: Language Models are Few-Shot Learners
        # "https://arxiv.org/pdf/2005.14165.pdf",
        # # LLaMA: Open and Efficient Foundation Language Models
        # "https://arxiv.org/pdf/2302.13971.pdf",
        # # Diffusion Models: Denoising Diffusion Probabilistic Models
        # "https://arxiv.org/pdf/2006.11239.pdf",
    ]

    @classmethod
    def get_llm(cls):
        """
        Initialize and return Gemini LLM instance
        using environment variables.
        """

        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env file")

        return ChatGoogleGenerativeAI(
            model=cls.GEMINI_MODEL,
            api_key=cls.GOOGLE_API_KEY,
            temperature=0.3,
        )
