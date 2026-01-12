from langchain_core.messages import SystemMessage, AIMessage
from src.core.models import get_model
from src.core.state import AgentState
from src.tools.search import global_tools

def call_business_intelligence_model(state: AgentState):
    print("[DEBUG] business_intelligence: INICIANDO")
    model = get_model().bind_tools(global_tools)

    prompt = SystemMessage(content=(
        "Eres un asistente de Business Intelligence experto y amigable. "
        "\n\nTUS RESPONSABILIDADES:"
        "\n1. CONVERSACIÓN GENERAL: Responde saludos, preguntas generales y mantén conversaciones naturales"
        "\n2. ANÁLISIS: Genera insights estratégicos, identifica tendencias, riesgos y oportunidades"
        "\n3. RECOMENDACIONES: Proporciona KPIs, métricas y acciones accionables"
        "\n4. UTILIZAR DATOS: Si hay información recopilada por el researcher, úsala para tu análisis"
        "\n\nESTILO DE COMUNICACIÓN:"
        "\n- Sé profesional pero cercano"
        "\n- Responde de forma clara y concisa"
        "\n- Para saludos, responde amablemente y ofrece ayuda"
        "\n- Para análisis, sé profundo y detallado"
        "\n\nRecuerda: Eres el agente principal del sistema, maneja todo tipo de conversaciones con profesionalismo."
    ))

    messages = state.get("messages", [])
    if not messages:
        print("[DEBUG] business_intelligence: No hay mensajes, retornando vacío")
        return {"messages": []}
    
    print(f"[DEBUG] business_intelligence: Procesando {len(messages)} mensajes")
    
    full_messages = [prompt] + messages
    response = model.invoke(full_messages)
    
    print(f"[DEBUG] business_intelligence: Respuesta del modelo:")
    print(f"  - Content: {getattr(response, 'content', 'N/A')[:150] if hasattr(response, 'content') else 'N/A'}")
    print(f"  - tool_calls: {len(getattr(response, 'tool_calls', []))} llamadas")
    
    # NO validar contenido si hay tool_calls
    if not response:
        print("[DEBUG] business_intelligence: No hay respuesta, retornando vacío")
        return {"messages": []}
    
    # Agregar metadata para identificar el agente
    if isinstance(response, AIMessage):
        response.name = "business_intelligence"
    
    print(f"[DEBUG] business_intelligence: Retornando mensaje")
    return {"messages": [response]}
