import json
from typing import Optional, Generator, Dict
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from src.api.schemas.chat_schemas import ChatRequest, ChatResponse
from src.api.services.agent_service import AgentService
from src.api.interfaces import Agent


class ChatService:
    """Servicio para gestionar conversaciones con agentes."""
    
    def __init__(self, agents: Dict[str, Agent], agent_service: AgentService):
        """
        Inicializa el servicio de chat con inyección de dependencias.
        
        Args:
            agents: Diccionario de agentes disponibles
            agent_service: Servicio de utilidades para agentes
        """
        self._agents = agents
        self._agent_service = agent_service
    
    async def chat(self, request: ChatRequest, agent_type: str = "supervisor") -> ChatResponse:
        """Procesa un mensaje y retorna la respuesta completa."""
        try:
            agent = self._get_agent(agent_type)
            inputs = self._agent_service.build_inputs(request)
            config = self._agent_service.build_config(request)
            
            result = await agent.ainvoke(inputs, config=config)
            
            final_message = result["messages"][-1].content
            
            return ChatResponse(
                response=final_message,
                thread_id=request.thread_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def chat_stream(self, request: ChatRequest, agent_type: str = "supervisor") -> StreamingResponse:
        """Procesa un mensaje y retorna un stream SSE."""
        agent = self._get_agent(agent_type)
        inputs = self._agent_service.build_inputs(request)
        config = self._agent_service.build_config(request)
        
        def event_generator() -> Generator[str, None, None]:
            last_message: Optional[str] = None
            try:
                for event in agent.stream(inputs, config=config):
                    # Extraer el último mensaje para el evento final
                    last_message = self._agent_service.extract_last_message(event) or last_message
                    
                    # Serializar eventos en el nuevo formato estructurado
                    structured_events = self._agent_service.serialize_event(event)
                    
                    # Enviar cada evento estructurado individualmente
                    for structured_event in structured_events:
                        yield f"data: {json.dumps(structured_event)}\n\n"
                        
            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
                return
            
            # Evento final con el último mensaje
            if last_message:
                done_payload = {"response": last_message, "thread_id": request.thread_id}
                yield f"event: final\ndata: {json.dumps(done_payload)}\n\n"
            
            yield "event: done\ndata: [DONE]\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    def _get_agent(self, agent_type: str) -> Agent:
        """Obtiene un agente del contenedor."""
        if agent_type not in self._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return self._agents[agent_type]
