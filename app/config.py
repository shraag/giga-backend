"""Game configuration and constants."""

# Canvas dimensions
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# Ball settings
BALL_RADIUS = 10
BALL_INITIAL_SPEED = 5
BALL_MAX_SPEED = 12

# Paddle settings
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_SPEED = 8
PADDLE_MARGIN = 30  # Distance from edge of canvas
PADDLE_HORIZONTAL_RANGE = 300  # Maximum distance paddle can move left/right from starting position

# Game settings
WINNING_SCORE = 5
TICK_RATE = 60  # FPS
TICK_INTERVAL = 1.0 / TICK_RATE  # Time between updates in seconds

# Player settings
MAX_PLAYERS = 2
RECONNECTION_TIMEOUT = 60  # Seconds to allow reconnection

# WebSocket settings
WS_HEARTBEAT_INTERVAL = 5  # Seconds between heartbeat checks
