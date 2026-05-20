from typing import Dict, List, Optional
from fastapi import WebSocket
import json
from app.core import get_logger

logger = get_logger("websocket")


class WebSocketManager:
    def __init__(self):
        self.user_connections: Dict[int, List[WebSocket]] = {}
        self.channel_connections: Dict[str, List[WebSocket]] = {}
        self.connection_user_map: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int, channel: str):
        connection_key = id(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        
        channel_key = f"{channel}:{user_id}"
        if channel not in self.channel_connections:
            self.channel_connections[channel] = []
        self.channel_connections[channel].append(websocket)
        
        self.connection_user_map[connection_key] = user_id
        
        logger.info(f"WebSocket connected: user_id={user_id}, channel={channel}, connections={len(self.user_connections[user_id])}")

    def disconnect(self, websocket: WebSocket):
        connection_key = id(websocket)
        user_id = self.connection_user_map.get(connection_key)
        
        if user_id is not None:
            if user_id in self.user_connections and websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                if len(self.user_connections[user_id]) == 0:
                    del self.user_connections[user_id]
            
            for channel, connections in list(self.channel_connections.items()):
                if websocket in connections:
                    connections.remove(websocket)
                    if len(connections) == 0:
                        del self.channel_connections[channel]
            
            del self.connection_user_map[connection_key]
            
            logger.info(f"WebSocket disconnected: user_id={user_id}, active_users={len(self.user_connections)}")

    async def send_to_user(self, user_id: int, message: dict):
        if user_id not in self.user_connections:
            logger.debug(f"No active connections for user_id={user_id}")
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_to_channel(self, channel: str, message: dict):
        if channel not in self.channel_connections:
            logger.debug(f"No active connections for channel={channel}")
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for websocket in self.channel_connections[channel]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send message to channel {channel}: {e}")
                disconnected.append(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        message_str = json.dumps(message)
        disconnected = []
        
        for user_id, connections in self.user_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {e}")
                    disconnected.append((user_id, websocket))
        
        for user_id, websocket in disconnected:
            self.disconnect(websocket)

    def get_user_connection_count(self, user_id: int) -> int:
        return len(self.user_connections.get(user_id, []))

    def get_total_connections(self) -> int:
        total = 0
        for connections in self.user_connections.values():
            total += len(connections)
        return total

    def get_active_users(self) -> int:
        return len(self.user_connections)


websocket_manager = WebSocketManager()