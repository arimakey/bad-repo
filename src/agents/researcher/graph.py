from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.core.state import AgentState
from src.tools.search import global_tools
from src.agents.researcher.nodes import call_researcher_model

# Inicializar el checkpointer para memoria persistente
memory = MemorySaver()

def create_researcher_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("researcher", call_researcher_model)
    workflow.add_node("tools", ToolNode(global_tools))
    
    workflow.add_edge("__start__", "researcher")
    
    def should_continue(state: AgentState):
        messages = state.get('messages', [])
        if not messages:
            return END
        
        last_message = messages[-1]
        
        # Si el último mensaje tiene tool_calls, ejecutar las tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Si es una ToolMessage (resultado de tool), volver a researcher para formatear respuesta
        if hasattr(last_message, 'type') and last_message.type == 'tool':
            return END
        
        return END

    workflow.add_conditional_edges("researcher", should_continue)
    workflow.add_edge("tools", "researcher")
    
    # Compilar con memoria persistente
    return workflow.compile(checkpointer=memory)

# Exportamos la instancia compilada
researcher_agent = create_researcher_graph()
