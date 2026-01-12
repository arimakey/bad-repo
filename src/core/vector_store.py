from abc import ABC, abstractmethod
from typing import List, Any
from langchain_core.documents import Document

class BaseVectorStore(ABC):
    """
    Interface abstracta para abstraer la base de datos vectorial.
    Permite cambiar de Pinecone a otras (Chroma, Weaviate, etc.) fácilmente.
    """
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Añade documentos a la base de datos."""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Busca documentos similares a una consulta."""
        pass

    @abstractmethod
    def delete_index(self) -> None:
        """Borra el índice o los datos."""
        pass
