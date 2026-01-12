import os
from typing import List
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from src.core.vector_store import BaseVectorStore

class PineconeStore(BaseVectorStore):
    def __init__(self, index_name: str = None):
        api_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        self.index = self.pc.Index(self.index_name)
        self.embeddings = OpenAIEmbeddings()

    def add_documents(self, documents: List[Document]) -> None:
        """Añade documentos convirtiéndolos primero a vectores."""
        vectors = []
        for i, doc in enumerate(documents):
            # Generar embedding del contenido
            embedding = self.embeddings.embed_query(doc.page_content)
            vectors.append({
                "id": f"doc_{i}", # O un ID más robusto
                "values": embedding,
                "metadata": {**doc.metadata, "text": doc.page_content}
            })
        self.index.upsert(vectors=vectors)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Busca documentos similares usando el cliente nativo."""
        query_embedding = self.embeddings.embed_query(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True
        )
        
        docs = []
        for match in results["matches"]:
            metadata = match["metadata"]
            text = metadata.pop("text", "")
            docs.append(Document(page_content=text, metadata=metadata))
        return docs

    def delete_index(self) -> None:
        """Limpia todos los vectores en el namesapce actual (simplificado)."""
        self.index.delete(delete_all=True)
