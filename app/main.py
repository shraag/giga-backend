"""FastAPI application with WebSocket support for Pong game."""

import asyncio
import json
import logging
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.connection_manager import ConnectionManager
from app.game_logic import GameEngine
from app.models import (
    PlayerInputMessage, PlayerConnectMessage, PingMessage,
    PlayerAssignmentMessage, GameEventMessage, ErrorMessage, PongMessage
)
from app.config import TICK_INTERVAL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Pong Game Server")

# Initialize game components
manager = ConnectionManager()
game = GameEngine()

# Game loop task
game_loop_task: Optional[asyncio.Task] = None


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the main game page."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "players_connected": manager.get_connected_player_count(),
        "game_active": game.game_active
    }


async def game_loop():
    """Main game loop that runs at 60 FPS."""
    logger.info("Game loop started")

    while True:
        try:
            # Clean up expired reconnection slots
            manager.cleanup_expired_reconnections()

            # Update game state
            event = game.update()

            # Broadcast game state to all players
            state = game.get_state()
            if state:
                await manager.broadcast_to_all(state.model_dump_json())

            # Send event messages if something notable happened
            if event:
                event_msg = GameEventMessage(
                    event_type=event["type"],
                    message=f"Player {event.get('scorer', '')} scored!" if event["type"] == "goal" else f"Player {event.get('winner', '')} wins!",
                    data=event
                )
                await manager.broadcast_to_all(event_msg.model_dump_json())

            # Wait for next tick
            await asyncio.sleep(TICK_INTERVAL)

        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            await asyncio.sleep(TICK_INTERVAL)


def start_game_loop_if_needed():
    """Start game loop if not already running."""
    global game_loop_task

    if game_loop_task is None or game_loop_task.done():
        game_loop_task = asyncio.create_task(game_loop())
        logger.info("Game loop started")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for game communication."""
    player_id: Optional[str] = None
    player_number: Optional[int] = None

    try:
        # Accept connection first
        await websocket.accept()

        # Wait for initial connection message
        data = await websocket.receive_text()
        connect_msg = json.loads(data)

        # Check if it's a reconnection
        reconnect_player_id = connect_msg.get("player_id")

        # Connect player
        try:
            player_id, player_number = await manager.connect(websocket, reconnect_player_id)
        except Exception as e:
            await websocket.send_text(
                ErrorMessage(message=str(e)).model_dump_json()
            )
            await websocket.close()
            return

        logger.info(f"Player {player_id} connected as Player {player_number}")

        # Send player assignment
        assignment = PlayerAssignmentMessage(
            player_id=player_id,
            player_number=player_number,
            message=f"You are Player {player_number}"
        )
        await websocket.send_text(assignment.model_dump_json())

        # Add player to game
        game.add_player(player_id, player_number)

        # Start game loop if both players are connected
        if manager.get_connected_player_count() == 2:
            start_game_loop_if_needed()

            # Notify both players that game is starting
            event = GameEventMessage(
                event_type="game_start",
                message="Game starting! Use W/S (Player 1) or Arrow Keys (Player 2) to move your paddle."
            )
            await manager.broadcast_to_all(event.model_dump_json())
        else:
            # Waiting for other player
            event = GameEventMessage(
                event_type="waiting",
                message="Waiting for another player to join..."
            )
            await websocket.send_text(event.model_dump_json())

        # Notify other players
        player_joined = GameEventMessage(
            event_type="player_joined",
            message=f"Player {player_number} joined the game"
        )
        await manager.broadcast(player_joined.model_dump_json(), exclude=player_id)

        # Listen for messages from client
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "input":
                # Handle player input
                input_msg = PlayerInputMessage(**message)
                game.handle_input(input_msg.player_id, input_msg.action)

            elif msg_type == "ping":
                # Respond to ping with pong
                pong = PongMessage()
                await websocket.send_text(pong.model_dump_json())

    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected")

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")

    finally:
        # Clean up connection
        if player_id:
            manager.disconnect(player_id)

            # Notify other players
            if player_number:
                game.remove_player(player_number)

                player_left = GameEventMessage(
                    event_type="player_left",
                    message=f"Player {player_number} left the game"
                )
                await manager.broadcast_to_all(player_left.model_dump_json())

                # Send waiting message if only one player left
                if manager.get_connected_player_count() == 1:
                    waiting = GameEventMessage(
                        event_type="waiting",
                        message="Waiting for another player to join..."
                    )
                    await manager.broadcast_to_all(waiting.model_dump_json())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
