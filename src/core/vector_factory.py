import os
from src.agents.researcher.pinecone_store import PineconeStore

class VectorStoreFactory:
    """Factory para crear instancias de vector stores."""
    
    @staticmethod
    def create(store_type: str = "pinecone"):
        """
        Crea una instancia de vector store según el tipo especificado.
        
        Args:
            store_type: Tipo de vector store ("pinecone", etc.)
            
        Returns:
            Instancia del vector store
        """
        if store_type == "pinecone":
            return PineconeStore()
        
        # Aquí se podrían añadir más implementaciones como ChromaStore, WeaverStore, etc.
        raise ValueError(f"Vector store type '{store_type}' no soportado.")

def get_vector_store(store_type: str = "pinecone"):
    """
    Factoría para obtener la implementación de base de datos vectorial configurada.
    (Función legacy, usar VectorStoreFactory.create() en su lugar)
    """
    return VectorStoreFactory.create(store_type)
