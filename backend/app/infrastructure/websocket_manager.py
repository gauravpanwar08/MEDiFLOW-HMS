import uuid
import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # doctor_id -> list of websocket connections
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, doctor_id: uuid.UUID):
        await websocket.accept()
        if doctor_id not in self.active_connections:
            self.active_connections[doctor_id] = []
        self.active_connections[doctor_id].append(websocket)

    def disconnect(self, websocket: WebSocket, doctor_id: uuid.UUID):
        if doctor_id in self.active_connections:
            if websocket in self.active_connections[doctor_id]:
                self.active_connections[doctor_id].remove(websocket)

            if not self.active_connections[doctor_id]:
                del self.active_connections[doctor_id]

    async def broadcast_to_doctor_queue(self, doctor_id: uuid.UUID, queue_data: list[dict]):
        if doctor_id in self.active_connections:
            message = json.dumps({
                "type": "QUEUE_UPDATE",
                "data": queue_data
            })

            dead_connections = []

            for connection in self.active_connections[doctor_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)

            # cleanup broken connections
            for conn in dead_connections:
                self.disconnect(conn, doctor_id)


manager = ConnectionManager()