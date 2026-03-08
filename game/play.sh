#!/bin/bash
# play.sh - Launch NinjaStrike on Raspberry Pi
# Run from baker repo root: ./game/play.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_BIN="$SCRIPT_DIR/NinjaStrike"

if [ ! -f "$GAME_BIN" ]; then
    echo "Game binary not found at $GAME_BIN"
    echo "Make sure you ran: git pull"
    exit 1
fi

chmod +x "$GAME_BIN"

echo "Launching NinjaStrike..."
exec "$GAME_BIN" "$@"
