#!/bin/bash

# Controller Test Script

echo "--- Detected Input Devices ---"
ls -l /dev/input/js* 2>/dev/null || echo "No joystick devices (jsX) found."
ls -l /dev/input/gamepad_* 2>/dev/null || echo "No custom gamepad symlinks found."

echo ""
echo "--- Testing Input (Press Ctrl+C to stop) ---"
echo "Testing first detected controller (/dev/input/js0)..."
if [ -e /dev/input/js0 ]; then
    jstest --event /dev/input/js0
else
    echo "/dev/input/js0 not found. Make sure controllers are connected."
fi
