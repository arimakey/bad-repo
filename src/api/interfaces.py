from typing import Protocol, Any, AsyncIterator


class Agent(Protocol):
    """Interfaz para agentes LangGraph."""
    
    async def ainvoke(self, inputs: dict, config: dict) -> dict:
        """Invoca el agente de forma asíncrona."""
        ...
    
    def stream(self, inputs: dict, config: dict) -> AsyncIterator[dict]:
        """Stream del agente."""
        ...


class IAgentService(Protocol):
    """Interfaz para servicio de agentes."""
    
    @staticmethod
    def build_inputs(request: Any) -> dict:
        """Construye inputs para el agente."""
        ...
    
    @staticmethod
    def build_config(request: Any) -> dict:
        """Construye configuración del agente."""
        ...
    
    @staticmethod
    def serialize_event(event: dict) -> dict:
        """Serializa evento del stream."""
        ...
    
    @staticmethod
    def extract_last_message(event: dict) -> str | None:
        """Extrae último mensaje del evento."""
        ...


class IChatService(Protocol):
    """Interfaz para servicio de chat."""
    
    async def chat(self, request: Any, agent_type: str) -> Any:
        """Procesa mensaje y retorna respuesta."""
        ...
    
    def chat_stream(self, request: Any, agent_type: str) -> Any:
        """Procesa mensaje y retorna stream SSE."""
        ...
