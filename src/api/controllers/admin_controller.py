from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from src.api.services.vector_service import VectorService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_vector_service() -> VectorService:
    """Dependency injection para VectorService."""
    return VectorService()


@router.get("/")
async def admin_page():
    """Sirve la página de administración para subir documentos."""
    static_path = Path(__file__).parent.parent / "static" / "index.html"
    if not static_path.exists():
        raise HTTPException(status_code=404, detail="Admin page not found")
    return FileResponse(static_path)


@router.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Endpoint para subir documentos y procesarlos en la vector DB.
    
    ADVERTENCIA: Este endpoint permite cargar documentos a la base vectorial.
    Debe estar protegido o comentado en producción.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    vector_service = get_vector_service()
    
    # Leer contenido de archivos
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))
    
    try:
        result = await vector_service.process_and_store_files(file_data)
        return {
            "message": "Documents processed successfully",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-stats")
async def vector_stats():
    """Obtiene estadísticas de la base de datos vectorial."""
    # Implementar según tu vector store
    return {
        "status": "ok",
        "message": "Vector DB stats endpoint - implement based on your vector store"
    }
