import faiss
import numpy as np
import requests
import psycopg2
from typing import List, Optional, Any
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from pydantic import Field, PrivateAttr
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    VectorStore that uses:
    - Pre-built FAISS index from embedding_engine
    - Embedding server API for query embeddings
    - PostgreSQL for fetching chunks and metadata
    """

    def __init__(
        self,
        faiss_index_path: str,
        embedding_server_url: str,
        database_url: str,
        embedding_dim: int = 768,
    ) -> None:
        """
        Initialize the FAISSVectorStore.

        Parameters
        ----------
        faiss_index_path : str
            Path to the FAISS index file (e.g., "embedding_engine/build/paper.faiss")
        embedding_server_url : str
            URL of the embedding server API (e.g., "http://localhost:8000")
        database_url : str
            PostgreSQL connection string
        embedding_dim : int
            Dimension of embeddings (default: 768 for BGE models)
        """
        # Resolve path - if relative, make it relative to project root
        faiss_path = Path(faiss_index_path)
        if not faiss_path.is_absolute():
            # Remove leading ./ if present
            clean_path = str(faiss_path).lstrip("./")
            faiss_path = Path(clean_path)
            
            # Try to resolve relative to current working directory first
            if not faiss_path.exists():
                # Try relative to project root (assuming we're in src/vectorstore/)
                project_root = Path(__file__).parent.parent.parent
                faiss_path = project_root / clean_path
                
            # If still doesn't exist, try as-is (might be relative to cwd)
            if not faiss_path.exists():
                faiss_path = Path(faiss_index_path)
                
        self.faiss_index_path = faiss_path.resolve()  # Resolve to absolute path
        self.embedding_server_url = embedding_server_url.rstrip("/")
        self.database_url = database_url
        self.embedding_dim = embedding_dim

        # Load FAISS index
        if not self.faiss_index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.faiss_index_path}. "
                f"Please check your FAISS_INDEX_PATH configuration. "
                f"Expected location: embedding_engine/build/paper.faiss"
            )

        logger.info(f"Loading FAISS index from {self.faiss_index_path}")
        self.index = faiss.read_index(str(self.faiss_index_path))

        if self.index.d != embedding_dim:
            raise ValueError(
                f"FAISS dimension mismatch: expected {embedding_dim}, got {self.index.d}"
            )

        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")

        # Initialize database connection
        self.conn = None
        self._connect_db()

        # Create retriever
        self.retriever = FAISSRetriever(vector_store=self, search_kwargs={"k": 4})

    def _connect_db(self):
        """Establish PostgreSQL connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _get_query_embedding(self, query: str) -> np.ndarray:
        """
        Get embedding for a query using the embedding server API.

        Parameters
        ----------
        query : str
            Query text

        Returns
        -------
        np.ndarray
            Normalized embedding vector (1, embedding_dim)
        """
        url = f"{self.embedding_server_url}/embed"

        payload = {
            "requests": [{"content": {"parts": [{"text": query}]}}],
            "is_query": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract embedding from response
            if "responses" not in data or len(data["responses"]) == 0:
                raise ValueError("No embedding in response")

            embedding_values = data["responses"][0]["embedding"]["values"]
            vec = np.array(embedding_values, dtype="float32").reshape(1, -1)

            # Normalize for cosine similarity
            faiss.normalize_L2(vec)

            logger.info(f"Got embedding from server: shape {vec.shape}")
            return vec

        except Exception as e:
            logger.error(f"Error getting embedding from server: {e}")
            raise

    def _fetch_chunks_by_ids(self, chunk_ids: List[int]) -> List[dict]:
        """
        Fetch chunks and metadata from PostgreSQL by chunk IDs.

        Parameters
        ----------
        chunk_ids : List[int]
            List of chunk IDs (FAISS IDs)

        Returns
        -------
        List[dict]
            List of dictionaries with chunk data and metadata
        """
        if not chunk_ids:
            return []

        # Query to fetch chunks with paper metadata
        # Use unnest to preserve order from FAISS search
        query = """
        SELECT 
            ec.id,
            ec.chunk_text,
            ec.chunk_index,
            ec.page_number,
            ec.document_id,
            rp.title as paper_title,
            rp.authors,
            rp.doi,
            rp.source
        FROM embedding_chunks ec
        LEFT JOIN research_papers rp ON ec.document_id = rp.id
        WHERE ec.id = ANY(%s)
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (chunk_ids,))
                rows = cur.fetchall()

                # Create a dictionary for fast lookup
                chunks_dict = {}
                for row in rows:
                    chunks_dict[row[0]] = {
                        "id": row[0],
                        "chunk_text": row[1],
                        "chunk_index": row[2],
                        "page_number": row[3],
                        "document_id": row[4],
                        "paper_title": row[5] or "Unknown",
                        "authors": row[6] or "Unknown",
                        "doi": row[7] or "",
                        "source": row[8] or "",
                    }

                # Preserve order from FAISS search results
                chunks = []
                for chunk_id in chunk_ids:
                    if chunk_id in chunks_dict:
                        chunks.append(chunks_dict[chunk_id])
                    else:
                        logger.warning(f"Chunk ID {chunk_id} not found in database")

                logger.info(f"Fetched {len(chunks)} chunks from database")
                return chunks

        except Exception as e:
            logger.error(f"Error fetching chunks from database: {e}")
            raise

    def search(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for similar documents using FAISS and return LangChain Documents.

        Parameters
        ----------
        query : str
            Query text
        k : int
            Number of documents to retrieve

        Returns
        -------
        List[Document]
            List of LangChain Document objects with content and metadata
        """
        # Get query embedding
        query_vec = self._get_query_embedding(query)

        # Print query vector
        print(f"\n{'='*60}")
        print("QUERY VECTOR:")
        print(f"{'='*60}")
        print(f"Shape: {query_vec.shape}")
        print(f"First 10 values: {query_vec[0][:10]}")
        print(f"Vector norm: {np.linalg.norm(query_vec)}")
        logger.info(f"Query vector shape: {query_vec.shape}")

        # Search FAISS
        scores, ids = self.index.search(query_vec, k)
        scores = scores[0]
        ids = ids[0].astype(int).tolist()

        print(f"\n{'='*60}")
        print("FAISS SEARCH RESULTS:")
        print(f"{'='*60}")
        print(f"Found {len(ids)} results")
        print(f"Top scores: {scores[:5]}")
        print(f"Top IDs: {ids[:5]}")
        logger.info(f"FAISS search returned {len(ids)} results")
        logger.info(f"Top scores: {scores[:5]}")
        logger.info(f"Top IDs: {ids[:5]}")

        # Fetch and print stored vectors from FAISS
        print(f"\n{'='*60}")
        print("STORED VECTORS FROM FAISS:")
        print(f"{'='*60}")
        for i, chunk_id in enumerate(ids[:5]):  # Print first 5 vectors
            try:
                # Reconstruct vector from FAISS index
                stored_vec = np.zeros(self.embedding_dim, dtype=np.float32)
                self.index.reconstruct(int(chunk_id), stored_vec)
                print(f"\nVector for Chunk ID {chunk_id}:")
                print(f"  Shape: {stored_vec.shape}")
                print(f"  First 10 values: {stored_vec[:10]}")
                print(f"  Vector norm: {np.linalg.norm(stored_vec)}")
                print(f"  Similarity score: {scores[i] if i < len(scores) else 'N/A'}")
            except Exception as e:
                print(f"  Could not reconstruct vector for ID {chunk_id}: {e}")

        # Fetch chunks from database
        chunks_data = self._fetch_chunks_by_ids(ids)

        # Convert to LangChain Documents
        documents = []
        for i, chunk_data in enumerate(chunks_data):
            # Create metadata
            metadata = {
                "chunk_id": chunk_data["id"],
                "document_id": chunk_data["document_id"],
                "chunk_index": chunk_data["chunk_index"],
                "page_number": chunk_data["page_number"],
                "paper_title": chunk_data["paper_title"],
                "authors": chunk_data["authors"],
                "doi": chunk_data["doi"],
                "source": chunk_data["source"],
                "similarity_score": float(scores[i]) if i < len(scores) else 0.0,
            }

            doc = Document(page_content=chunk_data["chunk_text"], metadata=metadata)
            documents.append(doc)

            # Print vector and chunk info
            print(f"\n{'='*60}")
            print(f"CHUNK {i+1}")
            print(f"{'='*60}")
            print(f"Chunk ID: {chunk_data['id']}")
            print(f"Similarity Score: {scores[i] if i < len(scores) else 'N/A'}")
            print(f"Paper Title: {chunk_data['paper_title']}")
            print(f"Authors: {chunk_data['authors']}")
            print(f"Document ID: {chunk_data['document_id']}")
            print(f"Page Number: {chunk_data['page_number']}")
            print(f"Chunk Index: {chunk_data['chunk_index']}")
            print(f"DOI: {chunk_data['doi']}")
            print(f"Source: {chunk_data['source']}")
            print(f"\nChunk Text (first 300 chars):")
            print(f"{chunk_data['chunk_text'][:300]}...")
            print(f"\nFull Chunk Text:")
            print(f"{chunk_data['chunk_text']}")
            print(f"{'='*60}\n")

            logger.info(f"\n--- Chunk {i+1} ---")
            logger.info(f"ID: {chunk_data['id']}")
            logger.info(f"Score: {scores[i] if i < len(scores) else 'N/A'}")
            logger.info(f"Paper: {chunk_data['paper_title']}")
            logger.info(f"Authors: {chunk_data['authors']}")
            logger.info(
                f"Chunk text (first 200 chars): {chunk_data['chunk_text'][:200]}..."
            )

        return documents

    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        Get a retriever instance.

        Parameters
        ----------
        search_kwargs : dict, optional
            Search parameters (e.g., {"k": 4})

        Returns
        -------
        FAISSRetriever
            Retriever instance
        """
        if search_kwargs:
            self.retriever.search_kwargs = search_kwargs
        return self.retriever

    def __del__(self):
        """Close database connection on deletion."""
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass  # Ignore errors during cleanup


class FAISSRetriever(BaseRetriever):
    """LangChain retriever wrapper for FAISSVectorStore."""
    
    # Use PrivateAttr for attributes that shouldn't be part of Pydantic model
    _vector_store: Any = PrivateAttr()
    search_kwargs: dict = Field(default_factory=lambda: {"k": 4})

    def __init__(self, vector_store: FAISSVectorStore, search_kwargs: dict = None, **kwargs):
        super().__init__(**kwargs)
        self._vector_store = vector_store
        if search_kwargs:
            self.search_kwargs = search_kwargs

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """Retrieve relevant documents for a query."""
        k = self.search_kwargs.get("k", 4)
        return self._vector_store.search(query, k=k)

    @property
    def vectorstore(self):
        """Return the underlying vector store."""
        return self._vector_store


# Keep the old VectorStore class for backward compatibility
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS as LangChainFAISS


class VectorStore:
    """
    Wrapper class for managing embeddings, vector storage, and retrieval of documents for a RAG (Retrieval-Augmented Generation) system.

    This class:
      - Loads a SentenceTransformer embedding model
      - Builds a vector store from documents
      - Exposes a retriever interface for semantic search
    """

    def __init__(self, embedding_model: str) -> None:
        """
        Initialize the VectorStore with an embedding model.

        Parameters
        ----------
        embedding_model : str (Name of the sentence-transformers Model)
        """
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectorstore = None
        self.retriever = None

    def create_retriever(
        self, documents: List[Document], search_kwargs: dict | None = None
    ) -> None:
        """
        Build a vector store from a list of documents and initialize the retriever.

        Parameters
        ----------
        documents : List[Document]
            List of LangChain Document objects containing text + metadata.
        search_kwargs : dict, optional
            Additional search parameters for the retriever (e.g., {"k": 4}).

        Notes
        -----
        - This must be called before semantic search.
        - Computes embeddings for all documents and stores them in FAISS.
        """
        self.vectorstore = LangChainFAISS.from_documents(
            documents, self.embedding_model
        )
        if search_kwargs is None:
            search_kwargs = {"k": 4}
        self.retriever = self.vectorstore.as_retriever(search_kwargs=search_kwargs)

    def get_retriever(self):
        """
        Return the initialized retriever instance.

        Returns
        -------
        BaseRetriever
            The retriever object used for semantic search.

        Raises
        ------
        ValueError
            If the retriever has not been initialized yet.
        """
        if self.retriever is None:
            raise ValueError("VectorStore not initialized.")
        return self.retriever

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieve the top-k most relevant documents for a given query.

        Parameters
        ----------
        query : str
            The user query to search for semantically.
        k : int, optional
            Number of documents to retrieve (default = 4).

        Returns
        -------
        List[Document]
            A list of top-k documents ranked by semantic similarity.

        Raises
        ------
        ValueError
            If the retriever has not been initialized.
        """
        if self.retriever is None:
            raise ValueError("VectorStore not initialized.")
        return self.retriever.invoke(query, k=k)
