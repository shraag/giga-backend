// Pong Game Client

class PongGame {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.ws = null;
        this.playerId = null;
        this.playerNumber = null;
        this.gameState = null;
        this.keysPressed = new Set();
        this.reconnecting = false;

        // Try to restore player ID from session
        this.playerId = sessionStorage.getItem('pong_player_id');

        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupKeyboardControls();
        this.startRenderLoop();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.updateStatus('Connecting to server...');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');

                // Send connection message (with player_id if reconnecting)
                const connectMsg = {
                    type: 'connect',
                    player_id: this.playerId
                };
                this.ws.send(JSON.stringify(connectMsg));
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection error');
            };

            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.updateStatus('Disconnected. Attempting to reconnect...');

                // Attempt to reconnect after 2 seconds
                setTimeout(() => {
                    if (!this.reconnecting) {
                        this.reconnecting = true;
                        this.connectWebSocket();
                    }
                }, 2000);
            };
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateStatus('Failed to connect to server');
        }
    }

    handleMessage(message) {
        const type = message.type;

        switch (type) {
            case 'assignment':
                this.playerId = message.player_id;
                this.playerNumber = message.player_number;
                sessionStorage.setItem('pong_player_id', this.playerId);
                this.updateStatus(message.message);
                this.addMessage(`You are Player ${this.playerNumber}`, 'info');
                this.reconnecting = false;
                break;

            case 'game_state':
                this.gameState = message;
                this.updateScores(message.scores);
                break;

            case 'event':
                this.handleGameEvent(message);
                break;

            case 'error':
                this.updateStatus('Error: ' + message.message);
                this.addMessage(message.message, 'error');
                break;

            case 'pong':
                // Heartbeat response
                break;

            default:
                console.log('Unknown message type:', type);
        }
    }

    handleGameEvent(event) {
        const eventType = event.event_type;

        switch (eventType) {
            case 'game_start':
                this.updateStatus('Game Active');
                this.addMessage(event.message, 'success');
                break;

            case 'goal':
                this.addMessage(event.message, 'info');
                break;

            case 'game_end':
                this.updateStatus('Game Over');
                this.addMessage(event.message, 'success');
                const winner = event.data.winner;
                if (winner === this.playerNumber) {
                    this.addMessage('You won!', 'success');
                } else {
                    this.addMessage('You lost!', 'error');
                }
                break;

            case 'waiting':
                this.updateStatus(event.message);
                this.addMessage(event.message, 'info');
                break;

            case 'player_joined':
                this.addMessage(event.message, 'info');
                break;

            case 'player_left':
                this.updateStatus('Waiting for player...');
                this.addMessage(event.message, 'info');
                break;
        }
    }

    setupKeyboardControls() {
        // Handle key down
        document.addEventListener('keydown', (e) => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

            const key = e.key.toLowerCase();

            // Prevent default for game keys
            if (['w', 's', 'a', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
                e.preventDefault();
            }

            // Check if this key is for this player
            let action = null;

            if (this.playerNumber === 1) {
                if (key === 'w') action = 'move_up';
                else if (key === 's') action = 'move_down';
                else if (key === 'a') action = 'move_left';
                else if (key === 'd') action = 'move_right';
            } else if (this.playerNumber === 2) {
                if (key === 'arrowup') action = 'move_up';
                else if (key === 'arrowdown') action = 'move_down';
                else if (key === 'arrowleft') action = 'move_left';
                else if (key === 'arrowright') action = 'move_right';
            }

            if (action && !this.keysPressed.has(key)) {
                this.keysPressed.add(key);
                this.sendInput(action);
            }
        });

        // Handle key up
        document.addEventListener('keyup', (e) => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

            const key = e.key.toLowerCase();

            // Check if this key is for this player
            const movementKeys = this.playerNumber === 1
                ? ['w', 's', 'a', 'd']
                : ['arrowup', 'arrowdown', 'arrowleft', 'arrowright'];

            if (movementKeys.includes(key) && this.keysPressed.has(key)) {
                this.keysPressed.delete(key);

                // Reset movement and reapply based on remaining pressed keys
                this.sendInput('stop');

                // Reapply any remaining movement keys
                if (this.playerNumber === 1) {
                    if (this.keysPressed.has('w')) this.sendInput('move_up');
                    else if (this.keysPressed.has('s')) this.sendInput('move_down');

                    if (this.keysPressed.has('a')) this.sendInput('move_left');
                    else if (this.keysPressed.has('d')) this.sendInput('move_right');
                } else if (this.playerNumber === 2) {
                    if (this.keysPressed.has('arrowup')) this.sendInput('move_up');
                    else if (this.keysPressed.has('arrowdown')) this.sendInput('move_down');

                    if (this.keysPressed.has('arrowleft')) this.sendInput('move_left');
                    else if (this.keysPressed.has('arrowright')) this.sendInput('move_right');
                }
            }
        });
    }

    sendInput(action) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.playerId) return;

        const message = {
            type: 'input',
            player_id: this.playerId,
            action: action
        };

        this.ws.send(JSON.stringify(message));
    }

    startRenderLoop() {
        const render = () => {
            this.render();
            requestAnimationFrame(render);
        };
        requestAnimationFrame(render);
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (!this.gameState) {
            // Draw waiting message
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Waiting for game state...', this.canvas.width / 2, this.canvas.height / 2);
            return;
        }

        // Draw center line
        this.ctx.strokeStyle = '#444';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([10, 10]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.canvas.width / 2, 0);
        this.ctx.lineTo(this.canvas.width / 2, this.canvas.height);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Draw ball
        const ball = this.gameState.ball;
        this.ctx.fillStyle = '#fff';
        this.ctx.beginPath();
        this.ctx.arc(ball.position.x, ball.position.y, ball.radius, 0, Math.PI * 2);
        this.ctx.fill();

        // Draw paddles
        this.drawPaddle(this.gameState.player1_paddle, this.playerNumber === 1);
        this.drawPaddle(this.gameState.player2_paddle, this.playerNumber === 2);
    }

    drawPaddle(paddle, isCurrentPlayer) {
        // Highlight current player's paddle
        this.ctx.fillStyle = isCurrentPlayer ? '#0f0' : '#fff';
        this.ctx.fillRect(
            paddle.position.x,
            paddle.position.y,
            paddle.width,
            paddle.height
        );
    }

    updateScores(scores) {
        document.getElementById('score-p1').textContent = scores.player1;
        document.getElementById('score-p2').textContent = scores.player2;
    }

    updateStatus(status) {
        document.getElementById('status').textContent = status;
    }

    addMessage(message, type = 'info') {
        const messagesDiv = document.getElementById('messages');
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;
        messagesDiv.insertBefore(messageEl, messagesDiv.firstChild);

        // Keep only last 5 messages
        while (messagesDiv.children.length > 5) {
            messagesDiv.removeChild(messagesDiv.lastChild);
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 5000);
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new PongGame();
});
