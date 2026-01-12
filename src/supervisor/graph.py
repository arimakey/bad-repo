from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from src.core.state import AgentState
from src.agents.researcher.nodes import call_researcher_model
from src.agents.business_intelligence.nodes import call_business_intelligence_model
from src.supervisor.nodes import (
    supervisor_node,
    agent_should_continue,
    route_after_tools,
)
from src.tools.search import global_tools

# Inicializar el checkpointer para memoria persistente
memory = MemorySaver()

def create_supervisor_graph():
    workflow = StateGraph(AgentState)
    
    # Nodos de los agentes
    workflow.add_node("researcher", call_researcher_model)
    workflow.add_node("business_intelligence", call_business_intelligence_model)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("tools", ToolNode(global_tools))
    
    # El supervisor decide quién empieza o sigue
    workflow.add_edge("__start__", "supervisor")
    
    # Mapa de decisiones del supervisor
    conditional_map = {
        "researcher": "researcher",
        "business_intelligence": "business_intelligence",
        "FINISH": END
    }
    
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    
    # Los agentes pueden ir a tools o volver al supervisor
    workflow.add_conditional_edges("researcher", agent_should_continue)
    workflow.add_conditional_edges("business_intelligence", agent_should_continue)
    
    # Después de ejecutar tools, volver al agente que las llamó
    workflow.add_conditional_edges("tools", route_after_tools)
    
    # Compilar con memoria persistente
    return workflow.compile(checkpointer=memory)

supervisor_agent = create_supervisor_graph()
