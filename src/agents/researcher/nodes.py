from langchain_core.messages import SystemMessage, AIMessage
from src.core.models import get_model
from src.core.state import AgentState
from src.tools.search import global_tools

def call_researcher_model(state: AgentState):
    """Lógica del nodo principal del investigador con instrucciones de sistema."""
    model = get_model().bind_tools(global_tools)
    
    messages = state.get("messages", [])
    if not messages:
        print("[DEBUG] researcher: No hay mensajes, retornando vacío")
        return {"messages": []}
    
    # Contar cuántas veces este agente ya actuó (mensajes con name='researcher')
    researcher_calls = sum(
        1 for msg in messages 
        if hasattr(msg, "name") and msg.name == "researcher"
    )
    
    # Verificar si hay un ToolMessage (resultado de web_search) en los últimos mensajes
    last_tool_message = None
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "tool":
            last_tool_message = msg
            break
    
    print(f"[DEBUG] researcher: researcher_calls={researcher_calls}, last_tool_message={'Sí' if last_tool_message else 'No'}")
    
    if last_tool_message and researcher_calls > 0:
        # Ya ejecutamos web_search y ya respondimos antes, reportar resultados finales
        print("[DEBUG] researcher: Ya hay resultados de tool Y ya actuamos antes, reportando finalmente")
        prompt = SystemMessage(content=(
            "Eres un investigador. Tienes los resultados de la búsqueda web. "
            "Resume brevemente los datos encontrados en 2-3 oraciones. "
            "Di algo como: 'Según la búsqueda realizada: [contenido del resultado]'"
        ))
    elif researcher_calls == 0:
        # Primera vez que actúa, DEBE llamar web_search
        print("[DEBUG] researcher: Primera actuación, DEBE llamar web_search")
        prompt = SystemMessage(content=(
            "Eres un investigador especializado. Tu ÚNICA tarea ahora es usar la herramienta web_search. "
            "\n\nOBLIGATORIO:"
            "\n- Identifica el tema clave de la pregunta del usuario"
            "\n- Llama a web_search con ese tema como query"
            "\n- NO intentes responder sin llamar primero a web_search"
            "\n\nEjemplo: Si preguntan 'precio de Apple', debes llamar web_search('precio de Apple')"
        ))
    else:
        # Caso extraño: ya actuamos pero no hay tool_message, reportar que no se encontró info
        print("[DEBUG] researcher: Situación inesperada, reportando sin datos")
        prompt = SystemMessage(content=(
            "No se pudieron obtener resultados de la búsqueda. Informa brevemente que no se pudo obtener la información."
        ))
    
    full_messages = [prompt] + messages
    response = model.invoke(full_messages)
    
    print(f"[DEBUG] researcher: Respuesta del modelo:")
    print(f"  - Content: {getattr(response, 'content', 'N/A')[:150] if hasattr(response, 'content') else 'N/A'}")
    print(f"  - tool_calls: {len(getattr(response, 'tool_calls', []))} llamadas")
    
    if not response:
        print("[DEBUG] researcher: No hay respuesta, retornando vacío")
        return {"messages": []}
    
    # Agregar metadata para identificar el agente
    if isinstance(response, AIMessage):
        response.name = "researcher"
    
    return {"messages": [response]}
