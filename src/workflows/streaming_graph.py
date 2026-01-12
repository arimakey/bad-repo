
from langgraph.graph import StateGraph, START, END
from src.agents.video_analysis import AgentState, analyze_video, decide_action, execute_action

def create_streaming_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("analyze", analyze_video)
    workflow.add_node("decide", decide_action)
    workflow.add_node("act", execute_action)
    
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "decide")
    workflow.add_edge("decide", "act")
    workflow.add_edge("act", END)
    
    return workflow.compile()

streaming_graph = create_streaming_graph()
