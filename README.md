# Giga Backend - Two-Player Pong Game

A real-time multiplayer Pong game built with Python (FastAPI) backend and JavaScript frontend. Players can control their paddles from separate browser tabs with real-time synchronization via WebSockets.

## Features

- Real-time two-player gameplay using WebSockets
- Server-authoritative game logic (60 FPS)
- Collision detection and physics simulation
- Score tracking and win conditions
- Reconnection support (60-second timeout)
- Clean, responsive web interface
- Keyboard controls for both players

## Architecture

### Backend (Python)
- **FastAPI**: Web framework with native WebSocket support
- **Game Engine**: Server-side physics, collision detection, and state management
- **Connection Manager**: WebSocket connection handling and player assignment
- **60 FPS Game Loop**: Authoritative game state updates

### Frontend (JavaScript)
- **HTML5 Canvas**: Game rendering
- **Native WebSockets**: Real-time communication
- **Keyboard Input**: W/S for Player 1, Arrow keys for Player 2

## Project Structure

```
giga-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app & WebSocket endpoint
│   ├── game_logic.py           # Game physics & collision detection
│   ├── models.py               # Pydantic models for messages
│   ├── connection_manager.py   # WebSocket connection handling
│   └── config.py               # Game constants
├── static/
│   ├── index.html              # Game interface
│   ├── game.js                 # Client-side game logic
│   └── styles.css              # Styling
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
└── README.md
```

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/shraag/giga-backend.git
   cd giga-backend
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv

   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env if you need to customize settings
   ```

## Running the Game

### Start the Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or alternatively:

```bash
python app/main.py
```

The server will start on `http://localhost:8000`

### Play the Game

1. Open your browser and go to: `http://localhost:8000`
2. Open a second browser tab/window (or use a different browser/device on the same network)
3. Go to the same URL: `http://localhost:8000`
4. Both players will be automatically assigned (Player 1 and Player 2)
5. The game will start when both players are connected

### Controls

**Player 1** (Left Paddle)
- `W` - Move Up
- `S` - Move Down

**Player 2** (Right Paddle)
- `↑` (Arrow Up) - Move Up
- `↓` (Arrow Down) - Move Down

### Game Rules

- First player to score 5 points wins
- Ball bounces off top and bottom walls
- Ball bounces off paddles with slight speed increase
- If ball goes past a paddle, the other player scores
- Ball resets to center after each goal

## Development

### Running in Development Mode with Auto-Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

Health check endpoint:
```bash
curl http://localhost:8000/health
```

### Configuration

Edit `app/config.py` to customize:
- Canvas dimensions
- Ball speed and physics
- Paddle size and speed
- Winning score
- Tick rate (FPS)
- Reconnection timeout

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, specify a different port:
```bash
uvicorn app.main:app --port 8080
```

### WebSocket Connection Issues
- Ensure firewall allows connections on the specified port
- Check that no proxy or VPN is interfering with WebSocket connections
- For remote connections, replace `localhost` with the server's IP address

### Game Not Starting
- Ensure both players are connected (check the status message)
- Check browser console for JavaScript errors
- Verify the server is running and accessible

## Technical Details

### WebSocket Message Protocol

**Client → Server:**
- `connect`: Initial connection/reconnection
- `input`: Paddle movement commands
- `ping`: Keep-alive heartbeat

**Server → Client:**
- `assignment`: Player number assignment
- `game_state`: Full game state (60 FPS)
- `event`: Game events (goal, game_start, game_end, etc.)
- `error`: Error messages
- `pong`: Heartbeat response

### Reconnection Logic
- Players receive a unique ID on first connection
- ID stored in browser sessionStorage
- If disconnected, players can reconnect within 60 seconds
- Game state preserved during reconnection window

## License

This project is for educational and demonstration purposes.

## Future Enhancements

Possible improvements:
- Multiple game rooms/lobbies
- Spectator mode
- Game replay functionality
- Leaderboard system
- Power-ups and obstacles
- Sound effects
- Mobile touch controls