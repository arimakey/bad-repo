from typing import Optional, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.api.schemas.chat_schemas import ChatRequest


class AgentService:
    """Servicio para gestionar agentes y configuración."""
    
    def __init__(self):
        self._previous_node = None
        self._last_supervisor_decision = None
    
    @staticmethod
    def build_inputs(request: ChatRequest) -> dict:
        """Construye los inputs para el agente."""
        return {"messages": [HumanMessage(content=request.message)]}
    
    @staticmethod
    def build_config(request: ChatRequest) -> dict:
        """Construye la configuración del agente."""
        return {
            "configurable": {"thread_id": request.thread_id},
            "recursion_limit": 25
        }
    
    def serialize_event(self, event: dict) -> List[Dict[str, Any]]:
        """
        Serializa un evento del stream en múltiples eventos estructurados.
        
        Returns:
            Lista de eventos en el formato esperado por el frontend
        """
        events: List[Dict[str, Any]] = []
        
        for node_name, values in event.items():
            # Ignorar nodos especiales
            if node_name.startswith("__"):
                continue
            
            # Procesar según el tipo de nodo
            if node_name == "supervisor":
                events.extend(self._process_supervisor_event(node_name, values))
            elif node_name == "tools":
                # Handoff del agente que llamó tools → tools
                if self._previous_node and self._previous_node != "tools":
                    events.append({
                        "type": "handoff",
                        "from": self._previous_node,
                        "to": "tools"
                    })
                events.extend(self._process_tools_event(values))
            elif node_name in ["researcher", "business_intelligence"]:
                # Handoff apropiado según de dónde viene
                if self._previous_node == "supervisor":
                    # supervisor → agente
                    events.append({
                        "type": "handoff",
                        "from": "supervisor",
                        "to": node_name
                    })
                elif self._previous_node == "tools":
                    # tools → agente (volviendo después de ejecutar tool)
                    events.append({
                        "type": "handoff",
                        "from": "tools",
                        "to": node_name
                    })
                
                events.extend(self._process_agent_event(node_name, values))
                
                # Si el agente no tiene tool_calls, volverá a supervisor
                # (detectamos esto viendo si tiene tool_calls en el último mensaje)
                messages = values.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    has_tool_calls = (isinstance(last_msg, AIMessage) and 
                                    hasattr(last_msg, "tool_calls") and 
                                    last_msg.tool_calls)
                    
                    if not has_tool_calls:
                        # El agente terminó sin tool_calls, volverá a supervisor
                        events.append({
                            "type": "handoff",
                            "from": node_name,
                            "to": "supervisor"
                        })
            
            self._previous_node = node_name
        
        return events
    
    def _process_supervisor_event(self, node_name: str, values: dict) -> List[Dict[str, Any]]:
        """Procesa eventos del supervisor."""
        events = []
        next_agent = values.get("next")
        
        if next_agent:
            self._last_supervisor_decision = next_agent
            
            if next_agent == "FINISH":
                events.append({
                    "type": "agent_message",
                    "agent": node_name,
                    "role": "system",
                    "kind": "routing",
                    "content": "Finalizando conversación"
                })
                events.append({
                    "type": "handoff",
                    "from": node_name,
                    "to": "END"
                })
            else:
                events.append({
                    "type": "agent_message",
                    "agent": node_name,
                    "role": "system",
                    "kind": "routing",
                    "content": f"Dirigiendo la consulta a {next_agent}"
                })
                # El handoff supervisor → agente se hará cuando procesemos el agente
        
        return events
    
    def _process_tools_event(self, values: dict) -> List[Dict[str, Any]]:
        """Procesa eventos de ejecución de tools."""
        events = []
        messages = values.get("messages", [])
        
        for msg in messages:
            if isinstance(msg, ToolMessage):
                events.append({
                    "type": "tool_result",
                    "tool_name": getattr(msg, "name", "unknown"),
                    "call_id": getattr(msg, "tool_call_id", ""),
                    "content": msg.content
                })
        
        return events
    
    def _process_agent_event(self, agent_name: str, values: dict) -> List[Dict[str, Any]]:
        """Procesa eventos de agentes (researcher, business_intelligence)."""
        events = []
        messages = values.get("messages", [])
        
        for msg in messages:
            if isinstance(msg, AIMessage):
                # Si tiene tool_calls, es un mensaje de reasoning
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Mensaje de reasoning (antes de llamar tools)
                    if msg.content:
                        events.append({
                            "type": "agent_message",
                            "agent": agent_name,
                            "role": "assistant",
                            "kind": "reasoning",
                            "content": msg.content or f"Ejecutando herramientas..."
                        })
                    
                    # Tool calls
                    for tool_call in msg.tool_calls:
                        events.append({
                            "type": "tool_call",
                            "tool_name": tool_call.get("name", "unknown"),
                            "tool_args": tool_call.get("args", {}),
                            "call_id": tool_call.get("id", "")
                        })
                else:
                    # Mensaje final (sin tool_calls)
                    if msg.content:
                        # Razonamiento interno del agente
                        events.append({
                            "type": "agent_message",
                            "agent": agent_name,
                            "role": "assistant",
                            "kind": "final",
                            "content": msg.content
                        })
                        
                        # Respuesta visible para el cliente
                        # Todos los mensajes finales generan agent_response
                        events.append({
                            "type": "agent_response",
                            "agent": agent_name,
                            "content": msg.content
                        })
        
        return events
    
    @staticmethod
    def extract_last_message(event: dict) -> Optional[str]:
        """Extrae el último mensaje de un evento."""
        for values in event.values():
            messages = values.get("messages") or []
            if messages:
                last_message = messages[-1]
                content = getattr(last_message, "content", "")
                # Solo retornar si tiene contenido y no es un mensaje con solo tool_calls
                if content:
                    return content
        return None
