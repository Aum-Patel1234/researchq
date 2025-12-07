from langchain_huggingface import HuggingFaceEmbeddings
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


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
        self.vectorstore = FAISS.from_documents(documents, self.embedding_model)
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
