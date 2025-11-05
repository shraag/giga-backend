"""Pydantic models for WebSocket messages and game state."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== Position and State Models ==========

class Position(BaseModel):
    """2D position."""
    x: float
    y: float


class Velocity(BaseModel):
    """2D velocity."""
    vx: float
    vy: float


class BallState(BaseModel):
    """State of the ball."""
    position: Position
    velocity: Velocity
    radius: float


class PaddleState(BaseModel):
    """State of a paddle."""
    position: Position
    width: float
    height: float
    player_id: str


class Scores(BaseModel):
    """Game scores."""
    player1: int = 0
    player2: int = 0


# ========== Client to Server Messages ==========

class PlayerInputMessage(BaseModel):
    """Message for player input."""
    type: Literal["input"] = "input"
    player_id: str
    action: Literal["move_up", "move_down", "move_left", "move_right", "stop"]


class PlayerConnectMessage(BaseModel):
    """Message when player connects."""
    type: Literal["connect"] = "connect"
    player_id: Optional[str] = None  # For reconnection


class PingMessage(BaseModel):
    """Ping message to keep connection alive."""
    type: Literal["ping"] = "ping"


# ========== Server to Client Messages ==========

class GameStateMessage(BaseModel):
    """Complete game state broadcast to clients."""
    type: Literal["game_state"] = "game_state"
    ball: BallState
    player1_paddle: PaddleState
    player2_paddle: PaddleState
    scores: Scores
    timestamp: float


class PlayerAssignmentMessage(BaseModel):
    """Assign player number to connected client."""
    type: Literal["assignment"] = "assignment"
    player_id: str
    player_number: int  # 1 or 2
    message: str


class GameEventMessage(BaseModel):
    """Game events like goals, game start/end."""
    type: Literal["event"] = "event"
    event_type: Literal["goal", "game_start", "game_end", "player_joined", "player_left", "waiting"]
    message: str
    data: Optional[dict] = None


class ErrorMessage(BaseModel):
    """Error message."""
    type: Literal["error"] = "error"
    message: str


class PongMessage(BaseModel):
    """Pong response to ping."""
    type: Literal["pong"] = "pong"
