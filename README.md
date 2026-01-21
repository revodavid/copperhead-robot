# CopperHead Robot

Autonomous robot player for the CopperHead 2-player Snake game.

**Server:** [copperhead-server](https://github.com/revodavid/copperhead-server) | **Client:** [copperhead-client](https://github.com/revodavid/copperhead-client)

## Features

- Connects to CopperHead server as an autonomous player
- AI with adjustable difficulty (1-10)
- Auto-reconnects between games
- Tracks win/loss statistics

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Connect to local server with default difficulty
python robot.py

# Connect to Codespaces server with difficulty 8
python robot.py --server wss://your-codespace-8000.app.github.dev/ws/ --difficulty 8
```

## Options

- `--server, -s`: Server WebSocket URL (default: `ws://localhost:8000/ws/`)
- `--difficulty, -d`: AI difficulty 1-10 (default: 5)

## License

MIT
