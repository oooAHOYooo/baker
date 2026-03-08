#!/bin/bash

# Autostart Hub Configurator
# This script sets up the Pi to boot directly into the Web Hub (Kiosk Mode)

set -e

echo "[+] Installing Flask and system requirements..."
sudo apt update
sudo apt install -y python3-flask chromium-browser x11-xserver-utils unclutter

echo "[+] Creating autostart directory..."
mkdir -p ~/.config/autostart

echo "[+] Creating hub_launcher.sh..."
cat <<EOF > ~/hub_launcher.sh
#!/bin/bash
# Start the Flask server
cd $(dirname "$0")/hub
python3 server.py &
HUB_PID=\$!

# Wait for server to start
sleep 5

# Launch Chromium in Kiosk mode
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000

# Cleanup on exit
kill \$HUB_PID
EOF
chmod +x ~/hub_launcher.sh

echo "[+] Adding to LXDE Autostart..."
cat <<EOF > ~/.config/autostart/baker_hub.desktop
[Desktop Entry]
Type=Application
Name=Baker Web Hub
Exec=/home/pi/hub_launcher.sh
EOF

echo "[+] Disabling screen sleep and cursor..."
# Add to ~/.config/lxsession/LXDE-pi/autostart if needed
if [ -f ~/.config/lxsession/LXDE-pi/autostart ]; then
    sed -i '/@xscreensaver/d' ~/.config/lxsession/LXDE-pi/autostart
    echo "@xset s off" >> ~/.config/lxsession/LXDE-pi/autostart
    echo "@xset -dpms" >> ~/.config/lxsession/LXDE-pi/autostart
    echo "@xset s noblank" >> ~/.config/lxsession/LXDE-pi/autostart
    echo "@unclutter -idle 0" >> ~/.config/lxsession/LXDE-pi/autostart
fi

echo "------------------------------------------------"
echo "  Autostart Setup Complete!"
echo "  The Hub will launch automatically on next boot."
echo "------------------------------------------------"
