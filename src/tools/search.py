from langchain_core.tools import tool
import os

# Configurar el wrapper de DuckDuckGo (no requiere API key)
search_wrapper = None
try:
    from duckduckgo_search import DDGS
    search_wrapper = DDGS()
    print("[INFO] DuckDuckGo search inicializado correctamente")
except ImportError as e:
    print(f"[WARNING] No se pudo importar duckduckgo_search: {e}")
    print("[WARNING] Las búsquedas usarán datos mock. Instale: poetry add duckduckgo-search")
except Exception as e:
    print(f"[WARNING] Error al inicializar DuckDuckGo: {e}")

@tool
def web_search(query: str) -> str:
    """Busca información en tiempo real en internet sobre cualquier tema, incluyendo precios de acciones, clima, noticias o datos específicos.
    
    Args:
        query: La consulta de búsqueda (ej: "precio de Apple", "clima en Madrid", "noticias tecnología")
    
    Returns:
        Resultados de búsqueda relevantes de internet
    """
    print(f"[DEBUG] web_search llamada con query: '{query}'")
    
    # Si DuckDuckGo no está disponible, usar datos mock
    if search_wrapper is None:
        print("[DEBUG] web_search: Usando datos mock (DuckDuckGo no disponible)")
        if "apple" in query.lower() or "aapl" in query.lower():
            return "Precio aproximado de Apple (AAPL): $180.50 USD. Nota: Esta es información de ejemplo. Para datos en tiempo real, configure DuckDuckGoSearch."
        if "sf" in query.lower() or "san francisco" in query.lower():
            return "Hace 15 grados y está nublado en San Francisco."
        return f"Resultado de búsqueda genérico para '{query}': 25 grados y sol. Nota: Configure DuckDuckGoSearch para búsquedas reales."
    
    try:
        # Realizar búsqueda real usando la API directa de duckduckgo_search
        results = search_wrapper.text(query, max_results=5)
        
        # Formatear resultados
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Sin título')
                body = result.get('body', '')
                formatted_results.append(f"{i}. {title}\n{body}")
            
            final_text = "\n\n".join(formatted_results)
            print(f"[DEBUG] web_search: Resultados obtenidos ({len(results)} resultados)")
            return final_text
        else:
            return "No se encontraron resultados para la búsqueda."
            
    except Exception as e:
        print(f"[ERROR] web_search: Error al buscar: {e}")
        return f"Error al realizar la búsqueda: {str(e)}. Por favor, intenta con otra consulta."

# Lista de herramientas disponibles globalmente
global_tools = [web_search]
