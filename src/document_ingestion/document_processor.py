import tempfile
from typing import List, Union
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
import requests
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pathlib import Path
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    PyPDFDirectoryLoader,
)


class DocumentProcessor:
    """Handle document loading and text chunking.

    Parameters:
        chunk_size (int): Maximum size of each text chunk.
        chunk_overlap (int): Overlap between chunks for smoother context.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def load_from_url(self, url: str) -> List[Document]:
        """Load an HTML page and convert it into documents.

        Parameters:
            url (str): Website URL to load.

        Returns:
            List[Document]: Extracted documents.
        """
        loader = WebBaseLoader(url)
        return loader.load()

    def load_from_pdf(self, file_path: Union[str, Path]) -> List[Document]:
        """Load PDF file from a local path.

        Parameters:
            file_path (str | Path): Path to the PDF file.

        Returns:
            List[Document]: Extracted PDF pages.
        """
        file_path = Path(file_path)
        loader = PyPDFDirectoryLoader(str(file_path))
        return loader.load()

    def load_pdf_from_url(self, url: str) -> List[Document]:
        """Download a PDF from a URL and load it into documents.

        Parameters:
            url (str): Direct link to a PDF file.

        Returns:
            List[Document]: Extracted pages from the downloaded PDF.
        """

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = Path(tmp.name)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp.close()

            return PyPDFLoader(str(pdf_path)).load()

        finally:
            if pdf_path.exists():
                os.remove(pdf_path)

    # TODO:
    # def load_document(self, sources:List[str])->List[Document]:
    #     pass

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """ " Split the Documents"""
        return self.splitter.split_documents(documents)
