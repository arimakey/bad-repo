from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.core.state import AgentState
from src.tools.search import global_tools
from src.agents.business_intelligence.nodes import call_business_intelligence_model

def create_bi_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("bi_analyst", call_business_intelligence_model)
    workflow.add_node("tools", ToolNode(global_tools))
    
    workflow.add_edge("__start__", "bi_analyst")
    
    def should_continue(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("bi_analyst", should_continue)
    workflow.add_edge("tools", "bi_analyst")
    
    return workflow.compile()

business_intelligence_agent = create_bi_graph()
