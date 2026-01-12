
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

class StreamService:
    def __init__(self):
        self.broadcaster: WebSocket | None = None
        self.viewers: List[WebSocket] = []
        self.current_risk_level: int = 0  # Memory state for risk escalation
        
        # Buffering state for analysis
        self.frame_buffer: List[bytes] = []
        self.last_analysis_time: float = 0
        self.frame_count: int = 0

    async def connect_broadcaster(self, websocket: WebSocket):
        await websocket.accept()
        self.broadcaster = websocket

    def disconnect_broadcaster(self):
        if self.broadcaster:
            # await self.broadcaster.close() # Often already closed
            self.broadcaster = None
            print("Broadcaster disconnected")

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)
        print(f"Viewer connected. Total: {len(self.viewers)}")

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.viewers:
            self.viewers.remove(websocket)
            print(f"Viewer disconnected. Total: {len(self.viewers)}")

    async def broadcast_frame(self, data: bytes):
        disconnected_viewers = []
        for viewer in self.viewers:
            try:
                await viewer.send_bytes(data)
            except (WebSocketDisconnect, Exception):
                disconnected_viewers.append(viewer)
        
        for viewer in disconnected_viewers:
            self.disconnect_viewer(viewer)

    async def process_frame(self, frame_data: bytes, analysis_callback):
        """
        Injest a frame from any source (WS or HTTP), broadcast it, and manage analysis buffer.
        """
        # 1. Broadcast LIVE
        await self.broadcast_frame(frame_data)
        
        # 2. Accumulate
        import time
        
        # Initialize timer on first frame
        if self.last_analysis_time == 0:
            self.last_analysis_time = time.time()
            
        self.frame_count += 1
        
        # Subsample for analysis
        # Since input is constrained to ~2 FPS (30 frames per 15s), we can buffer ALL frames 
        # or perhaps every 2nd frame if payload is too large. 
        # Let's keep 15 frames max per request roughly. 30/2 = 15.
        if self.frame_count % 2 == 0:
            self.frame_buffer.append(frame_data)
            
        # 3. Check Trigger (15s)
        current_time = time.time()
        if current_time - self.last_analysis_time >= 15:
            if self.frame_buffer:
                print(f"Triggering analysis for {len(self.frame_buffer)} frames...")
                frames_to_send = list(self.frame_buffer)
                self.frame_buffer.clear()
                self.last_analysis_time = current_time
                
                # Trigger callback (fire and forget task)
                import asyncio
                asyncio.create_task(analysis_callback(frames_to_send))
            else:
                self.last_analysis_time = current_time

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
