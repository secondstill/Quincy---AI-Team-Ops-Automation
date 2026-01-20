from fastapi import WebSocket
from typing import List, Dict
import json

class ConnectionManager:
    def __init__(self):
        # meeting_id -> List of {websocket, client_id}
        self.active_connections: Dict[str, List[Dict]] = {}

    async def connect(self, websocket: WebSocket, meeting_id: str, client_id: str):
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = []
        
        self.active_connections[meeting_id].append({"ws": websocket, "id": client_id})
        print(f"Client {client_id} connected to meeting {meeting_id}")

    def disconnect(self, websocket: WebSocket, meeting_id: str, client_id: str):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id] = [c for c in self.active_connections[meeting_id] if c["ws"] != websocket]
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
        print(f"Client {client_id} disconnected from meeting {meeting_id}")

    async def broadcast_to_others(self, message: dict, meeting_id: str, sender_id: str):
        if meeting_id in self.active_connections:
            for connection in self.active_connections[meeting_id]:
                if connection["id"] != sender_id:
                    await connection["ws"].send_text(json.dumps(message))

manager = ConnectionManager()
