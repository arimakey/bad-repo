
import os
import base64

from typing import TypedDict, Literal, List
from openai import OpenAI
from dotenv import load_dotenv
from src.services.action_service import ActionService

load_dotenv()

# Initialize OpenAI client pointing to OpenRouter
# Users can still use standard OpenAI by not setting OPENROUTER_BASE_URL (defaults to openai.com)
client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENROUTER_API_KEY", os.getenv("GOOGLE_API_KEY")) # Fallback to GOOGLE_KEY if that's what they set
)

MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-001")

class AgentState(TypedDict):
    frame_data: List[bytes]
    analysis: str
    risk_level: int
    previous_risk_level: int # Memory
    action_result: dict

def analyze_video(state: AgentState):
    frames = state["frame_data"]
    
    # Limit number of frames
    max_frames = 15
    if len(frames) > max_frames:
        step = len(frames) // max_frames
        frames = frames[::step][:max_frames]
    
    print(f"Analyzing video chunk with {len(frames)} frames...")

    content_parts = [{"type": "text", "text": "Describe objetivamente qué está sucediendo en esta secuencia de video. Sé detallado sobre cualquier movimiento, personas, o anomalías."}]
    
    for frame_bytes in frames:
        base64_image = base64.b64encode(frame_bytes).decode('utf-8')
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": content_parts}],
        )
        print(f"--- ANALYZE_VIDEO RESPONSE ---\n{response}\n------------------------------")
        analysis_text = response.choices[0].message.content
    except Exception as e:
        print(f"Analysis Error: {e}")
        analysis_text = "Error analyzing video frames."
        
    return {"analysis": analysis_text}

def decide_action(state: AgentState):
    analysis = state["analysis"]
    # Default to 0 if not present
    prev_level = state.get("previous_risk_level", 0) 
    
    prompt = f"""
    Actúa como un sistema de seguridad inteligente con memoria.
    
    NIVELES DE RIESGO DEFINIDOS:
    0: NORMALIDAD. No pasa nada. Área tranquila.
    1: VIGILANCIA. Algo se mueve o hay personas, pero comportamiento normal. Estoy "mirando".
    2: ALERTA VECINAL (SERENAZGO). Comportamiento sospechoso, ruidos, disturbio menor.
    3: ALERTA POLICIAL. Crimen visible, agresión física, robo, amenazas claras.
    4: EMERGENCIA MÉDICA (AMBULANCIA). Personas heridas, colapsadas, accidentes.
    5: PELIGRO FATAL. Armas visibles, tiroteo, cuerpo inerte, riesgo de muerte inminente.
    
    REGLA DE ESCALADA GRADUAL:
    - NO saltes de 0 a 5 de golpe, salvo evidencia extrema (arma disparando).
    - Lo ideal es subir paso a paso: 0 -> 1 -> 2 -> 3...
    - Si la situación se calma, puedes bajar de nivel o reiniciar a 0 (Falsa Alarma).
    - Tu nivel ANTERIOR fue: {prev_level}
    
    SITUACIÓN ACTUAL:
    {analysis}
    
    Basado en el nivel anterior ({prev_level}) y la situación actual, decide el NUEVO nivel (0-5).
    Retorna SOLO el número.
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print(f"--- DECIDE_ACTION RESPONSE ---\n{response}\n------------------------------")
        content = response.choices[0].message.content
        import re
        match = re.search(r'\d+', content)
        if match:
            risk_level = int(match.group())
        else:
            risk_level = prev_level # Maintain level if unsure
            
    except Exception as e:
        print(f"Decision Error: {e}")
        risk_level = prev_level

    # Clamp to 0-5
    risk_level = max(0, min(5, risk_level))
    
    return {"risk_level": risk_level}

def execute_action(state: AgentState):
    level = state["risk_level"]
    description = state["analysis"]
    
    if level == 0:
        result = ActionService.execute_level_0_action(description)
    elif level == 1:
        result = ActionService.execute_level_1_action(description)
    elif level == 2:
        result = ActionService.execute_level_2_action(description)
    elif level == 3:
        result = ActionService.execute_level_3_action(description)
    elif level == 4:
        result = ActionService.execute_level_4_action(description)
    elif level == 5:
        result = ActionService.execute_level_5_action(description)
    else:
        result = ActionService.execute_level_0_action(description)
        
    return {"action_result": result}
