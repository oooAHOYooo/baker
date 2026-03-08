#!/bin/bash

# Baker - Raspberry Pi 4 Game Setup Script
# This script installs all necessary dependencies for a Unity game on Pi 4
# including Bluetooth PS4 and USB Xbox 360 controller support.

set -e

echo "------------------------------------------------"
echo "  Baker: Raspberry Pi 4 Game Setup Started"
echo "------------------------------------------------"

# 1. Update System
echo "[+] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Controller & System Dependencies
echo "[+] Installing controller and system dependencies..."
sudo apt install -y \
    bluez \
    bluetooth \
    pi-bluetooth \
    joystick \
    jstest-gtk \
    evtest \
    libpulse0 \
    libasound2 \
    libglu1-mesa \
    xserver-xorg-input-all

# 3. Configure Bluetooth for Auto-Enable
echo "[+] Configuring Bluetooth..."
if [ -f /etc/bluetooth/main.conf ]; then
    sudo sed -i 's/#AutoEnable=false/AutoEnable=true/g' /etc/bluetooth/main.conf
    sudo sed -i 's/AutoEnable=false/AutoEnable=true/g' /etc/bluetooth/main.conf
fi
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# 4. Load xpad for Xbox 360 / Series X Controllers
echo "[+] Ensuring xpad (Xbox) is loaded..."
sudo modprobe xpad
if ! grep -q "xpad" /etc/modules; then
    echo "xpad" | sudo tee -a /etc/modules
fi

# 5. Setup udev rules for Gamepad Stability
echo "[+] Applying udev rules for controllers..."
cat <<EOF | sudo tee /etc/udev/rules.d/99-gamepad.rules
# Xbox 360 / One / Series X (Universal wired support)
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="028e", MODE="0666", SYMLINK+="input/gamepad_xbox"
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02d1", MODE="0666", SYMLINK+="input/gamepad_xbox"
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02dd", MODE="0666", SYMLINK+="input/gamepad_xbox"
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02e3", MODE="0666", SYMLINK+="input/gamepad_xbox"
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02ea", MODE="0666", SYMLINK+="input/gamepad_xbox"
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="0b12", MODE="0666", SYMLINK+="input/gamepad_xbox"

# PS4 DualShock 4 (Bluetooth)
SUBSYSTEM=="input", ATTRS{name}=="Wireless Controller", MODE="0666", SYMLINK+="input/gamepad_ps4"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger

# 6. HDMI Optimizations for TV (Check for Bookworm or Bullseye)
echo "[+] Suggesting HDMI optimizations in /boot/firmware/config.txt (if applicable)..."
# We won't auto-modify config.txt for safety, but we'll remind the user.

echo "------------------------------------------------"
echo "  Setup Complete!"
echo "------------------------------------------------"
echo "To pair your PS4 controller, run: ./bluetooth/pair_ps4.sh"
echo "To test your controllers, run: ./scripts/test_controllers.sh"
echo "------------------------------------------------"
