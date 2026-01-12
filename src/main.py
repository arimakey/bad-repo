from src.core.config import settings
from src.supervisor.graph import supervisor_agent
from langchain_core.messages import HumanMessage

def run():
    print(f"--- Ejecutando {settings.PROJECT_NAME} con Supervisor ---")
    
    # El supervisor decide qué agente usar (researcher o business_intelligence)
    inputs = {"messages": [HumanMessage(content="Analiza las métricas de ventas del Q4 y dame insights estratégicos")]}
    config = {"configurable": {"thread_id": "system_run_1"}}
    
    for event in supervisor_agent.stream(inputs, config=config):
        for node, values in event.items():
            print(f"Nodo Activo: {node}")
            if "messages" in values:
                print(f"Respuesta: {values['messages'][-1].content}")
            if "next" in values:
                print(f"Siguiente: {values['next']}")
        print("-" * 15)

if __name__ == "__main__":
    run()
