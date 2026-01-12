from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
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
    try:
        while True:
            data = await websocket.receive_bytes()
            # New centralized logic
            await stream_service.process_frame(data, run_analysis)
            
    except WebSocketDisconnect:
        stream_service.disconnect_broadcaster()
    except Exception as e:
        print(f"Broadcaster error: {e}")
        stream_service.disconnect_broadcaster()

@app.post("/api/upload_frame")
async def upload_frame(request: Request):
    """
    HTTP Endpoint for ESP32 (or other devices) to push frames without WebSocket.
    Expects raw binary body of the image (JPEG).
    """
    try:
        data = await request.body()
        if not data:
            return {"status": "error", "message": "empty body"}
        
        await stream_service.process_frame(data, run_analysis)
        return {"status": "ok"}
    except Exception as e:
        print(f"HTTP Upload Error: {e}")
        return {"status": "error", "detail": str(e)}

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
