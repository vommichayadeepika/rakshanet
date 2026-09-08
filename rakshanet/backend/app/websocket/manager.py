import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("rakshanet.websocket")


class ConnectionManager:
    """
    Manages active WebSocket client connections for real-time disaster coordination.
    Handles client registration, disconnection, and resilient JSON message broadcasting.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Sends a JSON message to a specific connected client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Failed to send personal websocket message: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcasts a JSON message to all currently connected clients.
        Gracefully identifies and prunes dead connections.
        """
        if not self.active_connections:
            return

        payload = json.dumps(message, default=str)
        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to client, removing: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    def broadcast_sync(self, message: Dict[str, Any]):
        """
        Synchronous wrapper to safely schedule broadcast on the running asyncio event loop.
        Safe to call from standard synchronous FastAPI router endpoints.
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError:
            try:
                asyncio.run(self.broadcast(message))
            except Exception as e:
                logger.warning(f"Could not broadcast sync: {e}")

    @property
    def count(self) -> int:
        return len(self.active_connections)


ws_manager = ConnectionManager()

