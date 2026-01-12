
from typing import List
from fastapi import WebSocket

class StreamService:
    def __init__(self):
        self.broadcaster: WebSocket | None = None
        self.viewers: List[WebSocket] = []
        self.current_risk_level: int = 0  # Memory state for risk escalation

    async def connect_broadcaster(self, websocket: WebSocket):
        await websocket.accept()
        self.broadcaster = websocket

    def disconnect_broadcaster(self):
        self.broadcaster = None

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.viewers:
            self.viewers.remove(websocket)

    async def broadcast_frame(self, data: bytes):
        disconnected_viewers = []
        for viewer in self.viewers:
            try:
                await viewer.send_bytes(data)
            except Exception:
                disconnected_viewers.append(viewer)
        
        for viewer in disconnected_viewers:
            self.disconnect_viewer(viewer)

    async def broadcast_alert(self, alert_data: dict):
        disconnected_viewers = []
        for viewer in self.viewers:
            try:
                await viewer.send_json(alert_data)
            except Exception:
                disconnected_viewers.append(viewer)
        
        for viewer in disconnected_viewers:
            self.disconnect_viewer(viewer)

stream_service = StreamService()
