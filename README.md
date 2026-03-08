# Baker — Raspberry Pi 4 Game Setup

This repository contains everything you need to set up a **Raspberry Pi 4** for a Unity-based game played on a TV, with support for **PS4 (Bluetooth)** and **Universal Xbox (USB)** controllers.

## 🛠 Features

- **One-Shot Install**: Core dependencies (Bluetooth, joystick tools, Unity runtime libs) installed via `setup.sh`.
- **PS4 Controller Support**: Dedicated pairing script to handle Bluetooth syncing.
- **Universal Xbox Support**: Automated `xpad` driver loading for **Xbox 360, Xbox One, and Xbox Series X/S**.
- **Controller Stability**: Custom udev rules to ensure controllers are recognized correctly.
- **HDMI Optimization**: Recommended settings for TV display.

## 🚀 Quick Start

### 1. Clone the Repo
On your Raspberry Pi:
```bash
git clone https://github.com/your-username/baker.git
cd baker
```

### 2. Run the Setup Script
This will update your system and install necessary drivers/libs.
```bash
chmod +x setup.sh
sudo ./setup.sh
```

### 3. Connect Controllers

#### Xbox (Wired)
Supports **Xbox 360, One, and Series X/S**. Just plug it into any USB port. It will be recognized automatically by the `xpad` driver.

#### PS4 DualShock 4 (Bluetooth)
Run the pairing helper:
```bash
./bluetooth/pair_ps4.sh
```
Follow the on-screen prompts (Hold **SHARE + PS Button** on the controller to enter pairing mode).

### 4. Test Everything
Verify both controllers are sending signals:
```bash
./scripts/test_controllers.sh
```

---

## 📺 TV / HDMI Optimization

To ensure the Pi displays correctly on a TV and handles audio over HDMI, you may need to edit `/boot/firmware/config.txt` (or `/boot/config.txt` on older OS versions).

Add or uncomment these lines:
```bash
hdmi_force_hotplug=1
hdmi_group=1
hdmi_mode=16  # 1080p 60Hz
dtparam=audio=on
```

## 🎮 Unity Note

In your Unity project using the **New Input System**:
- The PS4 controller will show up as `Gamepad` or `DualShock4GamepadHID`.
- The Xbox controller (360, One, or Series X) will show up as `XInputController` or `Gamepad`.
- Linux handles both simultaneously as `/dev/input/js0` and `/dev/input/js1`.

---

## 🎬 Filmmaker Web Hub (TV Interface)

The Web Hub provides a premium, "10-foot" interface designed for navigating your game and daily video drafts using only a controller.

### Features
- **Gamepad Navigation**: Move through the UI with the D-Pad or Left Stick.
- **Dailies Viewer**: Browse and play `.mp4`/`.mov` files from any plugged-in USB drive or the `/media/pi` folder.
- **Kiosk Mode**: Boot directly into the hub without seeing the Linux desktop.

### Starting the Hub Manually
```bash
cd hub
python3 server.py
# Open Chromium to http://localhost:5000
```

### Enable Autostart (Boot to Hub)
To make your Pi feel like a dedicated media center:
```bash
chmod +x scripts/autostart_hub.sh
./scripts/autostart_hub.sh
```

---

## 📂 Repo Structure

- `setup.sh`: Main installation script.
- `hub/`: The Web Hub source code (Python/HTML/JS).
- `bluetooth/pair_ps4.sh`: Helper for Bluetooth pairing.
- `scripts/`: Diagnostic and automation scripts.
