"""Game logic including physics, collision detection, and state management."""

import random
import time
from typing import Optional, Tuple
from app.config import (
    CANVAS_WIDTH, CANVAS_HEIGHT,
    BALL_RADIUS, BALL_INITIAL_SPEED, BALL_MAX_SPEED,
    PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED, PADDLE_MARGIN, PADDLE_HORIZONTAL_RANGE,
    WINNING_SCORE
)
from app.models import (
    Position, Velocity, BallState, PaddleState, Scores, GameStateMessage
)


class Ball:
    """Ball object with physics."""

    def __init__(self):
        self.position = Position(x=CANVAS_WIDTH / 2, y=CANVAS_HEIGHT / 2)
        self.velocity = Velocity(vx=0, vy=0)
        self.radius = BALL_RADIUS
        self.reset()

    def reset(self):
        """Reset ball to center with random direction."""
        self.position.x = CANVAS_WIDTH / 2
        self.position.y = CANVAS_HEIGHT / 2

        # Random angle between -45 and 45 degrees, or 135 and 225 degrees
        angle = random.choice([
            random.uniform(-45, 45),
            random.uniform(135, 225)
        ])
        angle_rad = angle * 3.14159 / 180

        self.velocity.vx = BALL_INITIAL_SPEED * (1 if angle < 90 or angle > 270 else -1)
        self.velocity.vy = BALL_INITIAL_SPEED * random.uniform(-1, 1)

    def update(self):
        """Update ball position based on velocity."""
        self.position.x += self.velocity.vx
        self.position.y += self.velocity.vy

    def bounce_vertical(self):
        """Reverse vertical velocity (bounce off top/bottom)."""
        self.velocity.vy *= -1

    def bounce_horizontal(self):
        """Reverse horizontal velocity (bounce off paddle)."""
        self.velocity.vx *= -1
        # Increase speed slightly on paddle hit, up to max
        speed = min(abs(self.velocity.vx) * 1.05, BALL_MAX_SPEED)
        self.velocity.vx = speed if self.velocity.vx > 0 else -speed

    def get_state(self) -> BallState:
        """Get current ball state."""
        return BallState(
            position=self.position,
            velocity=self.velocity,
            radius=self.radius
        )


class Paddle:
    """Paddle object controlled by player."""

    def __init__(self, player_id: str, player_number: int):
        self.player_id = player_id
        self.player_number = player_number
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.velocity_x = 0  # Horizontal velocity
        self.velocity_y = 0  # Vertical velocity

        # Position paddle on left or right side
        x = PADDLE_MARGIN if player_number == 1 else CANVAS_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH
        y = (CANVAS_HEIGHT - PADDLE_HEIGHT) / 2
        self.position = Position(x=x, y=y)

        # Store initial position for horizontal boundary checking
        self.initial_x = x

    def move_up(self):
        """Start moving paddle up."""
        self.velocity_y = -PADDLE_SPEED

    def move_down(self):
        """Start moving paddle down."""
        self.velocity_y = PADDLE_SPEED

    def move_left(self):
        """Start moving paddle left."""
        self.velocity_x = -PADDLE_SPEED

    def move_right(self):
        """Start moving paddle right."""
        self.velocity_x = PADDLE_SPEED

    def stop(self):
        """Stop paddle movement (both horizontal and vertical)."""
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self):
        """Update paddle position based on velocity."""
        # Update vertical position
        self.position.y += self.velocity_y

        # Keep paddle within vertical bounds
        if self.position.y < 0:
            self.position.y = 0
        elif self.position.y > CANVAS_HEIGHT - self.height:
            self.position.y = CANVAS_HEIGHT - self.height

        # Update horizontal position
        self.position.x += self.velocity_x

        # Keep paddle within horizontal bounds (limited range from starting position)
        min_x = self.initial_x - PADDLE_HORIZONTAL_RANGE
        max_x = self.initial_x + PADDLE_HORIZONTAL_RANGE

        if self.position.x < min_x:
            self.position.x = min_x
        elif self.position.x > max_x:
            self.position.x = max_x

    def get_state(self) -> PaddleState:
        """Get current paddle state."""
        return PaddleState(
            position=self.position,
            width=self.width,
            height=self.height,
            player_id=self.player_id
        )

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get paddle boundaries (left, right, top, bottom)."""
        return (
            self.position.x,
            self.position.x + self.width,
            self.position.y,
            self.position.y + self.height
        )


class GameEngine:
    """Main game engine managing state and physics."""

    def __init__(self):
        self.ball = Ball()
        self.player1_paddle: Optional[Paddle] = None
        self.player2_paddle: Optional[Paddle] = None
        self.scores = Scores(player1=0, player2=0)
        self.game_active = False
        self.winner: Optional[int] = None

    def add_player(self, player_id: str, player_number: int) -> Paddle:
        """Add a player and create their paddle."""
        paddle = Paddle(player_id, player_number)

        if player_number == 1:
            self.player1_paddle = paddle
        else:
            self.player2_paddle = paddle

        # Start game if both players are present
        if self.player1_paddle and self.player2_paddle:
            self.start_game()

        return paddle

    def remove_player(self, player_number: int):
        """Remove a player."""
        if player_number == 1:
            self.player1_paddle = None
        else:
            self.player2_paddle = None

        self.game_active = False

    def start_game(self):
        """Start or restart the game."""
        self.game_active = True
        self.winner = None
        self.scores = Scores(player1=0, player2=0)
        self.ball.reset()

    def check_collision_paddle(self, paddle: Paddle) -> bool:
        """Check if ball collides with paddle."""
        ball_left = self.ball.position.x - self.ball.radius
        ball_right = self.ball.position.x + self.ball.radius
        ball_top = self.ball.position.y - self.ball.radius
        ball_bottom = self.ball.position.y + self.ball.radius

        paddle_left, paddle_right, paddle_top, paddle_bottom = paddle.get_bounds()

        # Check if ball overlaps paddle
        return (
            ball_right >= paddle_left and
            ball_left <= paddle_right and
            ball_bottom >= paddle_top and
            ball_top <= paddle_bottom
        )

    def check_goal(self) -> Optional[int]:
        """Check if ball went out of bounds. Returns scoring player number or None."""
        if self.ball.position.x - self.ball.radius <= 0:
            # Ball went past left edge, player 2 scores
            return 2
        elif self.ball.position.x + self.ball.radius >= CANVAS_WIDTH:
            # Ball went past right edge, player 1 scores
            return 1
        return None

    def update(self) -> Optional[dict]:
        """Update game state. Returns event data if something notable happened."""
        if not self.game_active:
            return None

        event = None

        # Update ball position
        self.ball.update()

        # Check collision with top/bottom walls
        if self.ball.position.y - self.ball.radius <= 0 or \
           self.ball.position.y + self.ball.radius >= CANVAS_HEIGHT:
            self.ball.bounce_vertical()
            # Keep ball in bounds
            if self.ball.position.y - self.ball.radius < 0:
                self.ball.position.y = self.ball.radius
            else:
                self.ball.position.y = CANVAS_HEIGHT - self.ball.radius

        # Check collision with paddles
        if self.player1_paddle and self.check_collision_paddle(self.player1_paddle):
            self.ball.bounce_horizontal()
            # Adjust y velocity based on where ball hit paddle
            paddle_center = self.player1_paddle.position.y + self.player1_paddle.height / 2
            hit_pos = (self.ball.position.y - paddle_center) / (self.player1_paddle.height / 2)
            self.ball.velocity.vy = hit_pos * BALL_INITIAL_SPEED
            # Push ball out of paddle to prevent sticking
            self.ball.position.x = self.player1_paddle.position.x + self.player1_paddle.width + self.ball.radius

        if self.player2_paddle and self.check_collision_paddle(self.player2_paddle):
            self.ball.bounce_horizontal()
            # Adjust y velocity based on where ball hit paddle
            paddle_center = self.player2_paddle.position.y + self.player2_paddle.height / 2
            hit_pos = (self.ball.position.y - paddle_center) / (self.player2_paddle.height / 2)
            self.ball.velocity.vy = hit_pos * BALL_INITIAL_SPEED
            # Push ball out of paddle to prevent sticking
            self.ball.position.x = self.player2_paddle.position.x - self.ball.radius

        # Update paddle positions
        if self.player1_paddle:
            self.player1_paddle.update()
        if self.player2_paddle:
            self.player2_paddle.update()

        # Check for goals
        scorer = self.check_goal()
        if scorer:
            if scorer == 1:
                self.scores.player1 += 1
            else:
                self.scores.player2 += 1

            event = {
                "type": "goal",
                "scorer": scorer,
                "scores": {"player1": self.scores.player1, "player2": self.scores.player2}
            }

            # Check for winner
            if self.scores.player1 >= WINNING_SCORE:
                self.winner = 1
                self.game_active = False
                event["type"] = "game_end"
                event["winner"] = 1
            elif self.scores.player2 >= WINNING_SCORE:
                self.winner = 2
                self.game_active = False
                event["type"] = "game_end"
                event["winner"] = 2
            else:
                # Reset ball for next round
                self.ball.reset()

        return event

    def get_state(self) -> Optional[GameStateMessage]:
        """Get current game state as a message."""
        if not self.player1_paddle or not self.player2_paddle:
            return None

        return GameStateMessage(
            ball=self.ball.get_state(),
            player1_paddle=self.player1_paddle.get_state(),
            player2_paddle=self.player2_paddle.get_state(),
            scores=self.scores,
            timestamp=time.time()
        )

    def handle_input(self, player_id: str, action: str):
        """Handle player input."""
        # Find which paddle belongs to this player
        paddle = None
        if self.player1_paddle and self.player1_paddle.player_id == player_id:
            paddle = self.player1_paddle
        elif self.player2_paddle and self.player2_paddle.player_id == player_id:
            paddle = self.player2_paddle

        if not paddle:
            return

        # Update paddle velocity based on action
        if action == "move_up":
            paddle.move_up()
        elif action == "move_down":
            paddle.move_down()
        elif action == "move_left":
            paddle.move_left()
        elif action == "move_right":
            paddle.move_right()
        elif action == "stop":
            paddle.stop()
