from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import json

from src.core.config import settings
from src.api.controllers import chat_router, health_router, admin_router
from src.services.stream_service import stream_service
from src.workflows.streaming_graph import streaming_graph


def create_app() -> FastAPI:
    """Factory para crear y configurar la aplicación FastAPI."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Sistema multi-agente con LangGraph para BI e investigación"
    )
    
    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    
    # Montar archivos estáticos
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Registrar routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(admin_router)

    
    return app


app = create_app()

@app.get("/")
def read_root():
    return {"message": "Welcome to the LangGraph AI Agent API"}

@app.websocket("/ws/broadcast")
async def broadcast_endpoint(websocket: WebSocket):
    await stream_service.connect_broadcaster(websocket)
    
    frame_buffer = []
    last_analysis_time = 0
    # To avoid memory explosion, we'll sub-sample frames for storage
    # Assuming broadcast is ~15fps or more, we probably only need 1fps for analysis context
    # If using frame skipping logic here or in `analyze_video` (we did it in analyze_video already)
    # Let's just collect all and let the agent subsample, or do slight subsample here
    
    frame_count = 0 
    
    import time
    last_analysis_time = time.time()

    try:
        while True:
            data = await websocket.receive_bytes()
            # Broadcast raw frame to viewers (LIVE)
            await stream_service.broadcast_frame(data)
            
            # Accumulate for Analysis (every 5th frame ~ 3-5 FPS typically)
            frame_count += 1
            if frame_count % 5 == 0:
                frame_buffer.append(data)
            
            # Check if 15s passed
            current_time = time.time()
            if current_time - last_analysis_time >= 15:
                if frame_buffer:
                    print(f"Triggering analysis for {len(frame_buffer)} frames...")
                    # Copy buffer and clear
                    frames_to_send = list(frame_buffer)
                    frame_buffer.clear()
                    last_analysis_time = current_time
                    
                    asyncio.create_task(run_analysis(frames_to_send))
                else:
                    last_analysis_time = current_time # Reset timer even if empty
            
    except WebSocketDisconnect:
        stream_service.disconnect_broadcaster()
    except Exception as e:
        print(f"Broadcaster error: {e}")
        stream_service.disconnect_broadcaster()

@app.websocket("/ws/viewer")
async def viewer_endpoint(websocket: WebSocket):
    await stream_service.connect_viewer(websocket)
    try:
        while True:
            # Keep connection alive, though we mostly push data TO the viewer
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream_service.disconnect_viewer(websocket)


from typing import List

async def run_analysis(frame_data: List[bytes]):
    # Rate limiting: only analyze if we are ready (basic check could be added)
    # For now, we rely on the fact that LLM calls are slow so we might 
    # want to throttle this. Let's rely on Python's async scheduler for now.
    
    # Run the graph
    try:
        # Inject memory: Pass the current (now previous) risk level
        current_level = stream_service.current_risk_level
        print(f"Running analysis. Previous Risk Level: {current_level}")
        
        result = await streaming_graph.ainvoke({
            "frame_data": frame_data,
            "previous_risk_level": current_level
        })
        
        # Extract action result and updated risk level
        action_result = result.get("action_result")
        new_risk_level = result.get("risk_level", 0)
        
        # Update persistent state
        stream_service.current_risk_level = new_risk_level
        
        if action_result:
            await stream_service.broadcast_alert(action_result)
            
    except Exception as e:
        print(f"Analysis error: {e}")

def run_server():
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_server()
