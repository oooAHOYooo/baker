#!/bin/bash

# PS4 Controller Pairing Helper for Raspberry Pi

echo "------------------------------------------------"
echo "  PS4 Controller Pairing Helper"
echo "------------------------------------------------"
echo "1. Put your PS4 controller in pairing mode (Hold SHARE + PS button until it flashes white)."
echo "2. We will now scan for devices..."
echo ""

# Scan for a few seconds
timeout 10 bluetoothctl scan on || true

echo ""
echo "List of available devices:"
bluetoothctl devices

echo ""
echo "Enter the MAC address of your 'Wireless Controller' (e.g., 00:11:22:33:44:55):"
read -r MAC_ADDR

if [[ -z "$MAC_ADDR" ]]; then
    echo "No MAC address entered. Exiting."
    exit 1
fi

echo "Attempting to pair, trust, and connect to $MAC_ADDR..."
bluetoothctl pair "$MAC_ADDR"
bluetoothctl trust "$MAC_ADDR"
bluetoothctl connect "$MAC_ADDR"

echo "------------------------------------------------"
echo "Done! If successful, the controller light should turn solid blue."
echo "------------------------------------------------"
