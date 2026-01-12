import os
from langchain_openai import ChatOpenAI

def get_model(model_name: str = None, temperature: float = 0):
    """
    Factory para obtener instancias de LLMs preconfiguradas.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    target_model = model_name or os.getenv("OPENAI_MODEL_NAME", "google/gemini-1.5-flash:free")
    
    if not api_key or api_key == "your_openrouter_api_key_here":
        # Evitar fallos críticos en importación si la key no está configurada aún
        print("⚠️ Advertencia: OPENAI_API_KEY no configurada correctamente.")

    model = ChatOpenAI(
        model=target_model,
        temperature=temperature,
        openai_api_key=api_key,
        base_url=api_base if api_base else None,
        max_retries=3
    )
    
    return model
