#!/usr/bin/env python3
"""
CopperHead Robot - Autonomous Snake game player.

Connects to a CopperHead server and plays the game using AI.
"""

import asyncio
import json
import argparse
import websockets
from collections import deque

# Game constants (must match server)
GRID_WIDTH = 30
GRID_HEIGHT = 20


class RobotPlayer:
    """Autonomous player that connects to CopperHead server and plays using AI."""
    
    def __init__(self, server_url: str, difficulty: int = 5):
        self.server_url = server_url
        self.difficulty = max(1, min(10, difficulty))
        self.player_id = None
        self.game_state = None
        self.running = False
        self.wins = 0
        self.games_played = 0
        
    async def connect(self):
        """Connect to the game server."""
        # Try player 1 first, fall back to player 2
        for pid in [1, 2]:
            url = f"{self.server_url}{pid}"
            try:
                print(f"🐍 Connecting to {url}...")
                self.ws = await websockets.connect(url)
                self.player_id = pid
                print(f"✅ Connected as Player {pid}")
                return True
            except Exception as e:
                print(f"❌ Player {pid} failed: {e}")
        return False
    
    async def play(self):
        """Main game loop."""
        if not await self.connect():
            print("Failed to connect to server")
            return
            
        self.running = True
        
        # Send ready message
        await self.ws.send(json.dumps({
            "action": "ready",
            "mode": "two_player"
        }))
        print(f"🎮 Ready! Playing at difficulty {self.difficulty}")
        
        try:
            while self.running:
                message = await self.ws.recv()
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.ConnectionClosed:
            print("🔌 Connection closed")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False
            
    async def handle_message(self, data: dict):
        """Handle incoming server messages."""
        msg_type = data.get("type")
        
        if msg_type == "state":
            self.game_state = data.get("game")
            if self.game_state and self.game_state.get("running"):
                direction = self.calculate_move()
                if direction:
                    await self.ws.send(json.dumps({
                        "action": "move",
                        "direction": direction
                    }))
                    
        elif msg_type == "start":
            print("🚀 Game started!")
            
        elif msg_type == "gameover":
            self.games_played += 1
            winner = data.get("winner")
            if winner == self.player_id:
                self.wins += 1
                print(f"🏆 Won! ({self.wins}/{self.games_played} games)")
            elif winner:
                print(f"💀 Lost! ({self.wins}/{self.games_played} games)")
            else:
                print(f"🤝 Draw! ({self.wins}/{self.games_played} games)")
            
            # Auto-ready for next game
            await asyncio.sleep(1)
            await self.ws.send(json.dumps({
                "action": "ready",
                "mode": "two_player"
            }))
            print("🎮 Ready for next game!")
            
        elif msg_type == "waiting":
            print("⏳ Waiting for opponent...")
    
    def calculate_move(self) -> str | None:
        """Calculate the best move using AI logic."""
        if not self.game_state:
            return None
            
        snakes = self.game_state.get("snakes", {})
        my_snake = snakes.get(str(self.player_id))
        
        if not my_snake or not my_snake.get("body"):
            return None
            
        head = my_snake["body"][0]
        current_dir = my_snake.get("direction", "right")
        food = self.game_state.get("food")
        
        # Get opponent snake
        opponent_id = 2 if self.player_id == 1 else 1
        opponent = snakes.get(str(opponent_id))
        opponent_body = opponent.get("body", []) if opponent else []
        
        # Build set of dangerous positions
        dangerous = set()
        for snake_data in snakes.values():
            for segment in snake_data.get("body", []):
                dangerous.add((segment[0], segment[1]))
        
        # Possible moves
        directions = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        
        # Can't reverse
        opposites = {"up": "down", "down": "up", "left": "right", "right": "left"}
        
        # Evaluate each direction
        best_dir = None
        best_score = float('-inf')
        
        for direction, (dx, dy) in directions.items():
            # Can't reverse
            if direction == opposites.get(current_dir):
                continue
                
            new_x = (head[0] + dx) % GRID_WIDTH
            new_y = (head[1] + dy) % GRID_HEIGHT
            
            # Check if move is safe
            if (new_x, new_y) in dangerous:
                continue
                
            score = 0
            
            # Distance to food (closer is better)
            if food:
                food_dist = abs(new_x - food[0]) + abs(new_y - food[1])
                score += (GRID_WIDTH + GRID_HEIGHT - food_dist) * 10
            
            # Avoid edges at higher difficulties
            if self.difficulty >= 5:
                edge_dist = min(new_x, GRID_WIDTH - 1 - new_x, 
                               new_y, GRID_HEIGHT - 1 - new_y)
                score += edge_dist
            
            # Look-ahead collision check at higher difficulties
            if self.difficulty >= 7:
                future_safe = 0
                for future_dir, (fdx, fdy) in directions.items():
                    if future_dir == opposites.get(direction):
                        continue
                    fx = (new_x + fdx) % GRID_WIDTH
                    fy = (new_y + fdy) % GRID_HEIGHT
                    if (fx, fy) not in dangerous:
                        future_safe += 1
                score += future_safe * 5
            
            # Random factor based on difficulty (lower = more random)
            import random
            mistake_chance = (10 - self.difficulty) / 20
            if random.random() < mistake_chance:
                score -= random.randint(0, 50)
            
            if score > best_score:
                best_score = score
                best_dir = direction
        
        # If no safe move, try any non-reversing move
        if best_dir is None:
            for direction in directions:
                if direction != opposites.get(current_dir):
                    return direction
                    
        return best_dir


async def main():
    parser = argparse.ArgumentParser(description="CopperHead Robot Player")
    parser.add_argument("--server", "-s", default="ws://localhost:8000/ws/",
                        help="Server WebSocket URL (default: ws://localhost:8000/ws/)")
    parser.add_argument("--difficulty", "-d", type=int, default=5,
                        help="AI difficulty 1-10 (default: 5)")
    args = parser.parse_args()
    
    print("🤖 CopperHead Robot Player")
    print(f"   Server: {args.server}")
    print(f"   Difficulty: {args.difficulty}")
    print()
    
    robot = RobotPlayer(args.server, args.difficulty)
    await robot.play()


if __name__ == "__main__":
    asyncio.run(main())
