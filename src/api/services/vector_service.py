"""
Servicio para gestionar embeddings y almacenamiento vectorial.

Dependencias requeridas:
    pip install langchain-community unstructured pypdf python-docx langchain-text-splitters
"""

from typing import List
from pathlib import Path
import tempfile
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from src.core.vector_factory import VectorStoreFactory


class VectorService:
    """Servicio para gestionar embeddings y almacenamiento vectorial."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = VectorStoreFactory.create()
    
    async def process_and_store_files(self, files: List[tuple]) -> dict:
        """
        Procesa archivos subidos, crea embeddings y los almacena en vector DB.
        
        Args:
            files: Lista de tuplas (filename, content_bytes)
        
        Returns:
            Dict con información del procesamiento
        """
        total_chunks = 0
        processed_files = []
        
        for filename, content in files:
            try:
                # Guardar temporalmente el archivo
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(filename).suffix
                ) as tmp_file:
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                # Cargar documento según extensión
                documents = self._load_document(tmp_path, filename)
                
                # Dividir en chunks
                chunks = self.text_splitter.split_documents(documents)
                
                # Agregar metadata
                for chunk in chunks:
                    chunk.metadata["source"] = filename
                
                # Almacenar en vector DB
                self.vector_store.add_documents(chunks)
                
                total_chunks += len(chunks)
                processed_files.append({
                    "filename": filename,
                    "chunks": len(chunks)
                })
                
                # Limpiar archivo temporal
                Path(tmp_path).unlink()
                
            except Exception as e:
                processed_files.append({
                    "filename": filename,
                    "error": str(e)
                })
        
        return {
            "files_processed": len([f for f in processed_files if "error" not in f]),
            "total_chunks": total_chunks,
            "files": processed_files
        }
    
    def _load_document(self, file_path: str, filename: str):
        """Carga un documento según su extensión."""
        extension = Path(filename).suffix.lower()
        
        if extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif extension == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        elif extension == ".txt":
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return loader.load()
    
    async def search_similar(self, query: str, k: int = 5):
        """Busca documentos similares en la vector DB."""
        return self.vector_store.similarity_search(query, k=k)
