from typing import Dict
from functools import lru_cache

from src.api.interfaces import Agent
from src.api.services.agent_service import AgentService
from src.api.services.chat_service import ChatService
from src.supervisor.graph import supervisor_agent
from src.agents.business_intelligence.graph import business_intelligence_agent
from src.agents.researcher.graph import researcher_agent


class DependencyContainer:
    """Contenedor de dependencias para la aplicación."""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._agent_service: AgentService | None = None
        self._chat_service: ChatService | None = None
        self._initialize()
    
    def _initialize(self):
        """Inicializa las dependencias."""
        # Registrar agentes
        self._agents = {
            "supervisor": supervisor_agent,
            "bi": business_intelligence_agent,
            "researcher": researcher_agent,
        }
        
        # Registrar servicios
        self._agent_service = AgentService()
        self._chat_service = ChatService(
            agents=self._agents,
            agent_service=self._agent_service
        )
    
    def get_agent(self, agent_type: str) -> Agent:
        """Obtiene un agente por tipo."""
        if agent_type not in self._agents:
            raise ValueError(f"Agent type '{agent_type}' not found")
        return self._agents[agent_type]
    
    def get_agent_service(self) -> AgentService:
        """Obtiene el servicio de agentes."""
        if self._agent_service is None:
            raise RuntimeError("AgentService not initialized")
        return self._agent_service
    
    def get_chat_service(self) -> ChatService:
        """Obtiene el servicio de chat."""
        if self._chat_service is None:
            raise RuntimeError("ChatService not initialized")
        return self._chat_service


# Singleton del contenedor
@lru_cache()
def get_container() -> DependencyContainer:
    """Retorna la instancia singleton del contenedor."""
    return DependencyContainer()
