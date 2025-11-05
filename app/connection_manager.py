"""WebSocket connection manager for handling player connections."""

import time
import uuid
from typing import Dict, Optional
from fastapi import WebSocket
from app.config import MAX_PLAYERS, RECONNECTION_TIMEOUT


class ConnectionManager:
    """Manages WebSocket connections and player assignments."""

    def __init__(self):
        # Active connections: player_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # Player assignments: player_id -> player_number (1 or 2)
        self.player_assignments: Dict[str, int] = {}

        # Reverse mapping: player_number -> player_id
        self.player_slots: Dict[int, str] = {}

        # Disconnection tracking: player_id -> disconnect_time
        self.disconnected_players: Dict[str, float] = {}

    def is_full(self) -> bool:
        """Check if game is full (2 players connected)."""
        return len(self.active_connections) >= MAX_PLAYERS

    def get_available_slot(self) -> Optional[int]:
        """Get available player slot (1 or 2), or None if full."""
        if 1 not in self.player_slots:
            return 1
        if 2 not in self.player_slots:
            return 2
        return None

    async def connect(self, websocket: WebSocket, player_id: Optional[str] = None) -> tuple[str, int]:
        """
        Connect a new player or reconnect existing player.
        Returns (player_id, player_number).
        Note: WebSocket should already be accepted before calling this method.
        """
        # Check for reconnection
        if player_id and player_id in self.disconnected_players:
            # Player is reconnecting
            disconnect_time = self.disconnected_players[player_id]
            if time.time() - disconnect_time <= RECONNECTION_TIMEOUT:
                # Reconnection allowed
                player_number = self.player_assignments[player_id]
                self.active_connections[player_id] = websocket
                self.player_slots[player_number] = player_id
                del self.disconnected_players[player_id]
                return player_id, player_number

        # Check if game is full
        if self.is_full():
            raise Exception("Game is full")

        # New connection
        if not player_id:
            player_id = str(uuid.uuid4())

        # Assign player to available slot
        player_number = self.get_available_slot()
        if player_number is None:
            raise Exception("No available slots")

        self.active_connections[player_id] = websocket
        self.player_assignments[player_id] = player_number
        self.player_slots[player_number] = player_id

        return player_id, player_number

    def disconnect(self, player_id: str):
        """Disconnect a player and mark for potential reconnection."""
        if player_id in self.active_connections:
            del self.active_connections[player_id]
            self.disconnected_players[player_id] = time.time()

        # Remove from player slots but keep assignment for reconnection
        player_number = self.player_assignments.get(player_id)
        if player_number and player_number in self.player_slots:
            del self.player_slots[player_number]

    def cleanup_expired_reconnections(self):
        """Remove expired reconnection slots."""
        current_time = time.time()
        expired = [
            player_id for player_id, disconnect_time in self.disconnected_players.items()
            if current_time - disconnect_time > RECONNECTION_TIMEOUT
        ]

        for player_id in expired:
            del self.disconnected_players[player_id]
            if player_id in self.player_assignments:
                del self.player_assignments[player_id]

    def get_player_number(self, player_id: str) -> Optional[int]:
        """Get player number for a given player_id."""
        return self.player_assignments.get(player_id)

    def get_connected_player_count(self) -> int:
        """Get number of currently connected players."""
        return len(self.active_connections)

    async def send_to_player(self, player_id: str, message: str):
        """Send message to specific player."""
        if player_id in self.active_connections:
            websocket = self.active_connections[player_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude: Optional[str] = None):
        """Broadcast message to all connected players except excluded one."""
        for player_id, websocket in self.active_connections.items():
            if player_id != exclude:
                await websocket.send_text(message)

    async def broadcast_to_all(self, message: str):
        """Broadcast message to all connected players."""
        for websocket in self.active_connections.values():
            await websocket.send_text(message)
