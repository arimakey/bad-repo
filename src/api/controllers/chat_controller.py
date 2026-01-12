from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.schemas.chat_schemas import ChatRequest, ChatResponse
from src.api.services.chat_service import ChatService
from src.api.dependencies import get_container, DependencyContainer

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(
    container: DependencyContainer = Depends(get_container)
) -> ChatService:
    """Dependency injection para ChatService."""
    return container.get_chat_service()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    Endpoint para interactuar con el sistema multi-agente vía supervisor.
    """
    return await service.chat(request, agent_type="supervisor")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    """
    Stream del sistema multi-agente con supervisor.
    """
    return service.chat_stream(request, agent_type="supervisor")
