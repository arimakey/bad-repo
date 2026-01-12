from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Estado compartido que fluye entre agentes.
    """
    messages: Annotated[list, add_messages]
    next: str
    # Aquí puedes añadir campos globales como 'user_id', 'task_status', etc.
