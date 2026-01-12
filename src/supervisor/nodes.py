from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel

from src.core.models import get_model
from src.core.state import AgentState

members = ["researcher", "business_intelligence"]
options = ["FINISH"] + members

system_prompt = (
    "Eres un supervisor encargado de gestionar una conversación entre los siguientes trabajadores: {members}. "
    "Dada la siguiente solicitud del usuario, responde con el trabajador que debe actuar a continuación. "
    "\n\nAGENTES DISPONIBLES:"
    "\n- 'business_intelligence': Agente PRINCIPAL. Maneja conversaciones generales, saludos, análisis, recomendaciones estratégicas. Es el agente por defecto."
    "\n- 'researcher': Solo para búsquedas de información en tiempo real (precios actuales, noticias recientes, clima, datos del momento)."
    "\n\nREGLAS DE DECISIÓN:"
    "\n1. Saludos, conversación general, preguntas de análisis → 'business_intelligence'"
    "\n2. Preguntas que requieren datos actuales en tiempo real → 'researcher' primero, luego 'business_intelligence'"
    "\n3. Después de 'researcher': SIEMPRE envía a 'business_intelligence' para análisis"
    "\n4. Después de 'business_intelligence': SIEMPRE responde FINISH"
    "\n5. NUNCA envíes al mismo agente dos veces consecutivas"
    "\n\nEjemplos:"
    "\n- 'Hola' → business_intelligence → FINISH"
    "\n- 'Buenos días' → business_intelligence → FINISH"
    "\n- '¿Cómo estás?' → business_intelligence → FINISH"
    "\n- 'Precio de Apple hoy' → researcher → business_intelligence → FINISH"
    "\n- 'Analiza esta situación' → business_intelligence → FINISH"
)

class RouteResponse(BaseModel):
    next: Literal["researcher", "business_intelligence", "FINISH"]

def supervisor_node(state: AgentState):
    messages = state.get("messages", [])
    
    # Si no hay mensajes, terminar
    if not messages:
        print("[DEBUG] supervisor: No hay mensajes, terminando")
        return {"next": "FINISH"}
    
    # Contar cuántas veces cada agente ya actuó (incluyendo mensajes vacíos pero con name)
    researcher_count = sum(1 for msg in messages if hasattr(msg, "name") and msg.name == "researcher")
    bi_count = sum(1 for msg in messages if hasattr(msg, "name") and msg.name == "business_intelligence")
    
    print(f"[DEBUG] supervisor: researcher_count={researcher_count}, bi_count={bi_count}, total_messages={len(messages)}")
    
    # Debug: mostrar los últimos 3 mensajes
    for i, msg in enumerate(messages[-3:]):
        msg_name = getattr(msg, "name", "sin-name")
        msg_type = getattr(msg, "type", "sin-tipo")
        msg_content = getattr(msg, "content", "")[:50] if hasattr(msg, "content") else ""
        print(f"[DEBUG] supervisor: msg[-{3-i}]: type={msg_type}, name={msg_name}, content={msg_content}")
    
    # Si BI ya actuó al menos una vez, terminar
    if bi_count >= 1:
        print("[DEBUG] supervisor: Business intelligence ya actuó, terminando")
        return {"next": "FINISH"}
    
    # Si researcher ya actuó al menos 2 veces, enviar a BI
    if researcher_count >= 2:
        print("[DEBUG] supervisor: Researcher ya actuó 2+ veces, enviando a business_intelligence")
        return {"next": "business_intelligence"}
    
    # Si solo hay el mensaje del usuario (no hay agentes que hayan actuado)
    # Dejar que el modelo LLM decida, pero con el nuevo prompt que favorece BI por defecto
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Dada la conversación anterior, ¿quién debería actuar a continuación? "
            "Selecciona uno de: {options}. "
            f"\nCONTEXTO: researcher actuó {researcher_count} veces, business_intelligence {bi_count} veces. "
            "\nRECUERDA: business_intelligence es el agente PRINCIPAL para conversaciones generales.",
        ),
    ]).partial(options=str(options), members=", ".join(members))

    model = get_model()
    supervisor_chain = prompt | model.with_structured_output(RouteResponse)
    
    result = supervisor_chain.invoke(state)
    print(f"[DEBUG] supervisor: Decisión del modelo: {result.next}")
    return {"next": result.next}


def agent_should_continue(state: AgentState) -> str:
    """
    Determina si un agente debe ejecutar tools o volver al supervisor.
    
    Returns:
        "tools" si hay tool_calls pendientes, "supervisor" en caso contrario
    """
    messages = state.get("messages", [])
    if not messages:
        print("[DEBUG] agent_should_continue: No hay mensajes, volviendo a supervisor")
        return "supervisor"
    
    last_message = messages[-1]
    
    # Debug: imprimir información del último mensaje
    print(f"[DEBUG] agent_should_continue - Último mensaje:")
    print(f"  - Tipo: {getattr(last_message, 'type', 'sin tipo')}")
    print(f"  - Tiene tool_calls: {hasattr(last_message, 'tool_calls')}")
    if hasattr(last_message, 'tool_calls'):
        print(f"  - tool_calls: {last_message.tool_calls}")
        print(f"  - Cantidad de tool_calls: {len(last_message.tool_calls) if last_message.tool_calls else 0}")
    
    # Si el último mensaje tiene tool_calls, ejecutar tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[DEBUG] agent_should_continue: Detectados {len(last_message.tool_calls)} tool_calls, yendo a 'tools'")
        return "tools"
    
    # Si el último mensaje es ToolMessage, volver al supervisor
    if hasattr(last_message, "type") and last_message.type == "tool":
        print("[DEBUG] agent_should_continue: Último mensaje es ToolMessage, volviendo a supervisor")
        return "supervisor"
    
    # Por defecto, volver al supervisor
    print("[DEBUG] agent_should_continue: Sin tool_calls, volviendo a supervisor")
    return "supervisor"


def route_after_tools(state: AgentState) -> str:
    """
    Determina a qué agente volver después de ejecutar tools.
    
    Busca el último AI message con tool_calls para identificar
    qué agente inició la llamada a tools usando el campo 'name'.
    
    Returns:
        El nombre del agente que hizo la llamada a tools, o "supervisor" si no se puede determinar
    """
    messages = state.get("messages", [])
    
    print(f"[DEBUG] route_after_tools: Buscando agente que llamó tools entre {len(messages)} mensajes")
    
    # Buscar hacia atrás el último mensaje AI con tool_calls
    for i, msg in enumerate(reversed(messages)):
        if (
            hasattr(msg, "type") 
            and msg.type == "ai" 
            and hasattr(msg, "tool_calls") 
            and msg.tool_calls
        ):
            # Verificar si el mensaje tiene metadata 'name' para identificar el agente
            if hasattr(msg, "name") and msg.name:
                agent_name = msg.name
                print(f"[DEBUG] route_after_tools: Encontrado mensaje con name='{agent_name}' en posición -{i}")
                # Validar que el agente existe en nuestra lista
                if agent_name in members:
                    print(f"[DEBUG] route_after_tools: Retornando agente '{agent_name}'")
                    return agent_name
            
            # Si no tiene nombre, asumir que es researcher (compatibilidad)
            print(f"[DEBUG] route_after_tools: Mensaje sin 'name', asumiendo researcher")
            return "researcher"
    
    # Si no se encuentra, volver al supervisor
    print("[DEBUG] route_after_tools: No se encontró mensaje con tool_calls, volviendo a supervisor")
    return "supervisor"
