#!/usr/bin/env python3
"""
Baker Power Menu — Raspberry Pi 4 TV Interface
Navigate with Arrow Keys, select with Enter, go back with Backspace/Q
"""

import curses
import os
import subprocess
import sys
import time
import glob
import shutil
import socket
import platform

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

BAKER_DIR = os.path.dirname(os.path.realpath(__file__))
GAME_BINARY = os.environ.get("GAME_BINARY", "/home/pi/game/my_game.x86_64")
MEDIA_ROOTS = ["/media/pi", "/media", "/mnt"]

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".m4v", ".wmv")

VIDEO_PLAYERS = ["mpv", "vlc", "omxplayer", "mplayer", "ffplay"]


def find_video_player():
    for p in VIDEO_PLAYERS:
        if shutil.which(p):
            return p
    return None


def find_usb_videos():
    videos = []
    for root_dir in MEDIA_ROOTS:
        if os.path.isdir(root_dir):
            for dirpath, _, filenames in os.walk(root_dir):
                for f in filenames:
                    if f.lower().endswith(VIDEO_EXTS):
                        videos.append(os.path.join(dirpath, f))
    return sorted(videos)


def get_pi_model():
    try:
        with open("/proc/device-tree/model", "r") as f:
            return f.read().strip().replace("\x00", "")
    except Exception:
        return platform.machine() or "Unknown"


def get_os_info():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return platform.platform()


def get_cpu_temp():
    paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
    ]
    for p in paths:
        try:
            with open(p) as f:
                return f"{int(f.read().strip()) / 1000:.1f}°C"
        except Exception:
            pass
    return "N/A"


def get_cpu_freq():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
            return f"{int(f.read().strip()) / 1000:.0f} MHz"
    except Exception:
        return "N/A"


def get_memory():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem = {}
        for line in lines:
            k, v = line.split(":", 1)
            mem[k.strip()] = int(v.split()[0])
        total_mb = mem["MemTotal"] // 1024
        avail_mb = mem["MemAvailable"] // 1024
        used_mb = total_mb - avail_mb
        return f"{used_mb} MB / {total_mb} MB used"
    except Exception:
        return "N/A"


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No network"


def get_uptime():
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        h, m = divmod(int(secs), 3600)
        m //= 60
        return f"{h}h {m}m"
    except Exception:
        return "N/A"


def get_disk():
    try:
        usage = shutil.disk_usage("/")
        used_gb = usage.used / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        return f"{used_gb:.1f} GB / {total_gb:.1f} GB used"
    except Exception:
        return "N/A"


def get_controllers():
    devices = glob.glob("/dev/input/js*")
    if not devices:
        return "None detected"
    names = []
    for d in devices:
        try:
            result = subprocess.run(
                ["udevadm", "info", "--query=property", d],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.splitlines():
                if "ID_MODEL=" in line:
                    names.append(line.split("=", 1)[1])
                    break
            else:
                names.append(os.path.basename(d))
        except Exception:
            names.append(os.path.basename(d))
    return ", ".join(names)


def get_bluetooth_status():
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "bluetooth"],
            capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip()
    except Exception:
        return "N/A"


# ──────────────────────────────────────────────────────────────
# Curses Drawing
# ──────────────────────────────────────────────────────────────

def setup_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)   # selected
    curses.init_pair(2, curses.COLOR_CYAN,  -1)                   # header
    curses.init_pair(3, curses.COLOR_GREEN, -1)                   # ok / label
    curses.init_pair(4, curses.COLOR_YELLOW,-1)                   # warning
    curses.init_pair(5, curses.COLOR_RED,   -1)                   # error
    curses.init_pair(6, curses.COLOR_WHITE, -1)                   # normal


def draw_border(win):
    win.border()


def draw_header(win, title, subtitle=""):
    h, w = win.getmaxyx()
    win.clear()
    draw_border(win)
    banner = f"  BAKER PI  —  {title}  "
    try:
        win.addstr(1, (w - len(banner)) // 2, banner, curses.color_pair(2) | curses.A_BOLD)
    except curses.error:
        pass
    if subtitle:
        try:
            win.addstr(2, (w - len(subtitle)) // 2, subtitle, curses.color_pair(6))
        except curses.error:
            pass
    try:
        win.addstr(3, 2, "─" * (w - 4), curses.color_pair(2))
    except curses.error:
        pass


def draw_footer(win, hint="↑↓ Navigate   Enter Select   Q Back"):
    h, w = win.getmaxyx()
    try:
        win.addstr(h - 2, (w - len(hint)) // 2, hint, curses.color_pair(4))
    except curses.error:
        pass


def pick_menu(stdscr, title, items, subtitle="", back_label="← Back"):
    """Generic scrollable menu. Returns index of selected item (or -1 for back)."""
    curses.curs_set(0)
    setup_colors()
    h, w = stdscr.getmaxyx()
    all_items = [back_label] + list(items)
    sel = 1  # start on first real item

    scroll_offset = 0
    visible = h - 8  # rows available for items

    while True:
        stdscr.clear()
        draw_header(stdscr, title, subtitle)
        draw_footer(stdscr)

        for i, item in enumerate(all_items):
            row = 4 + i - scroll_offset
            if row < 4 or row > h - 3:
                continue
            label = f"  {'►' if i == sel else ' '}  {item}  "
            if i == sel:
                try:
                    stdscr.addstr(row, 2, label.ljust(w - 4)[:w - 4], curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                attr = curses.color_pair(3) if i == 0 else curses.color_pair(6)
                try:
                    stdscr.addstr(row, 2, label[:w - 4], attr)
                except curses.error:
                    pass

        stdscr.refresh()
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')):
            sel = max(0, sel - 1)
        elif key in (curses.KEY_DOWN, ord('j')):
            sel = min(len(all_items) - 1, sel + 1)
        elif key in (curses.KEY_ENTER, ord('\n'), ord('\r'), ord(' ')):
            if sel == 0:
                return -1
            return sel - 1
        elif key in (ord('q'), ord('Q'), curses.KEY_BACKSPACE, 127):
            return -1

        # Scroll to keep selection visible
        if sel - scroll_offset >= visible:
            scroll_offset = sel - visible + 1
        elif sel < scroll_offset:
            scroll_offset = sel


def message_screen(stdscr, title, lines, wait=True):
    """Show info screen, wait for key if wait=True."""
    setup_colors()
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    draw_header(stdscr, title)
    row = 5
    for line in lines:
        if row >= h - 3:
            break
        try:
            stdscr.addstr(row, 4, str(line)[:w - 6], curses.color_pair(6))
        except curses.error:
            pass
        row += 1
    hint = "Press any key to continue..." if wait else ""
    draw_footer(stdscr, hint)
    stdscr.refresh()
    if wait:
        stdscr.getch()


def run_shell_screen(stdscr, title, cmd, sudo=False):
    """Run a shell command full-screen and wait for key."""
    curses.endwin()
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")
    if sudo and os.geteuid() != 0:
        full_cmd = ["sudo"] + cmd if isinstance(cmd, list) else f"sudo {cmd}"
    else:
        full_cmd = cmd
    if isinstance(full_cmd, list):
        subprocess.run(full_cmd)
    else:
        os.system(full_cmd)
    print(f"\n{'='*60}")
    print("  Done. Press Enter to return to menu...")
    print(f"{'='*60}")
    input()
    stdscr.refresh()
    setup_colors()


# ──────────────────────────────────────────────────────────────
# Screens
# ──────────────────────────────────────────────────────────────

def screen_diagnostics(stdscr):
    """Show full system diagnostics."""
    lines = [
        f"  Model     : {get_pi_model()}",
        f"  OS        : {get_os_info()}",
        f"  Python    : {sys.version.split()[0]}",
        "",
        f"  CPU Temp  : {get_cpu_temp()}",
        f"  CPU Freq  : {get_cpu_freq()}",
        f"  Memory    : {get_memory()}",
        f"  Disk      : {get_disk()}",
        f"  Uptime    : {get_uptime()}",
        "",
        f"  IP Addr   : {get_ip()}",
        f"  Bluetooth : {get_bluetooth_status()}",
        f"  Controllers: {get_controllers()}",
        "",
        f"  Baker Dir : {BAKER_DIR}",
        f"  Game Path : {GAME_BINARY}",
        f"  Game Found: {'YES ✓' if os.path.exists(GAME_BINARY) else 'NOT FOUND'}",
    ]
    message_screen(stdscr, "System Diagnostics", lines)


def screen_daily_watcher(stdscr):
    """Scan USB drives for video files and play selection."""
    player = find_video_player()

    while True:
        # Rescan each time we return to this menu
        message_screen(stdscr, "Daily Watcher", ["Scanning for videos on USB drives..."], wait=False)
        time.sleep(0.3)
        videos = find_usb_videos()

        if not videos:
            message_screen(stdscr, "Daily Watcher", [
                "No video files found.",
                "",
                "Make sure your USB drive is mounted under:",
                "  /media/pi  or  /media  or  /mnt",
                "",
                "Supported: .mp4  .mov  .mkv  .avi  .m4v  .wmv",
            ])
            return

        display_names = []
        for v in videos:
            # Shorten path for display
            short = v
            for root in MEDIA_ROOTS:
                if v.startswith(root):
                    short = v[len(root):].lstrip("/")
                    break
            size_mb = os.path.getsize(v) / (1024 * 1024)
            display_names.append(f"{short}  [{size_mb:.1f} MB]")

        subtitle = f"{len(videos)} video(s) found | Player: {player or 'NOT FOUND'}"
        idx = pick_menu(stdscr, "Daily Watcher — USB Videos", display_names, subtitle=subtitle)

        if idx == -1:
            return

        chosen = videos[idx]

        if not player:
            message_screen(stdscr, "No Video Player", [
                "No video player found. Install one with:",
                "  sudo apt install mpv",
                "  sudo apt install vlc",
                "  sudo apt install omxplayer",
            ])
            return

        # Play video
        curses.endwin()
        print(f"\nPlaying: {chosen}")
        print("Press Q inside the player to quit.\n")
        if player == "omxplayer":
            subprocess.run(["omxplayer", "--aspect-mode", "stretch", chosen])
        elif player == "mpv":
            subprocess.run(["mpv", "--fs", "--really-quiet", chosen])
        elif player == "vlc":
            subprocess.run(["vlc", "--fullscreen", "--play-and-exit", chosen])
        else:
            subprocess.run([player, chosen])
        stdscr.refresh()
        setup_colors()
        # Loop back to list after playing


def screen_launch_game(stdscr):
    if not os.path.exists(GAME_BINARY):
        message_screen(stdscr, "Launch Game", [
            f"Game binary not found:",
            f"  {GAME_BINARY}",
            "",
            "Set environment variable GAME_BINARY to the correct path,",
            "or copy your Unity build to /home/pi/game/my_game.x86_64",
        ])
        return
    curses.endwin()
    print(f"\nLaunching game: {GAME_BINARY}")
    subprocess.Popen([GAME_BINARY])
    print("Game launched in background. Returning to menu...\n")
    time.sleep(1)
    stdscr.refresh()
    setup_colors()


def screen_web_hub(stdscr):
    items = [
        "Start Web Hub (port 5000)",
        "Enable Autostart (boot to hub)",
        "Stop Web Hub",
    ]
    while True:
        idx = pick_menu(stdscr, "Filmmaker Web Hub", items,
                        subtitle="Browser interface for game + dailies")
        if idx == -1:
            return
        if idx == 0:
            run_shell_screen(stdscr, "Starting Web Hub",
                             ["python3", os.path.join(BAKER_DIR, "hub", "server.py")])
        elif idx == 1:
            script = os.path.join(BAKER_DIR, "scripts", "autostart_hub.sh")
            run_shell_screen(stdscr, "Enable Autostart",
                             ["bash", script], sudo=True)
        elif idx == 2:
            run_shell_screen(stdscr, "Stop Web Hub",
                             ["pkill", "-f", "hub/server.py"])


def screen_controllers(stdscr):
    items = [
        "Pair PS4 Controller (Bluetooth)",
        "Test All Controllers",
        "Load Xbox xpad Driver",
        "Show Connected Controllers",
    ]
    while True:
        idx = pick_menu(stdscr, "Controller Setup", items)
        if idx == -1:
            return
        if idx == 0:
            script = os.path.join(BAKER_DIR, "bluetooth", "pair_ps4.sh")
            run_shell_screen(stdscr, "PS4 Bluetooth Pairing", ["bash", script])
        elif idx == 1:
            script = os.path.join(BAKER_DIR, "scripts", "test_controllers.sh")
            run_shell_screen(stdscr, "Test Controllers", ["bash", script])
        elif idx == 2:
            run_shell_screen(stdscr, "Load xpad Driver",
                             ["sudo", "modprobe", "xpad"])
        elif idx == 3:
            devices = glob.glob("/dev/input/js*") + glob.glob("/dev/input/event*")
            info = []
            for d in sorted(devices):
                info.append(f"  {d}")
            if not info:
                info = ["  No /dev/input/js* devices found."]
            message_screen(stdscr, "Connected Controllers", info)


def screen_setup(stdscr):
    items = [
        "Run Full Setup (setup.sh)",
        "Apply HDMI Optimizations",
        "Update System Packages",
        "Install mpv Video Player",
        "Install Python Flask (for Hub)",
    ]
    while True:
        idx = pick_menu(stdscr, "System Setup", items,
                        subtitle="Runs scripts from the Baker repo")
        if idx == -1:
            return
        if idx == 0:
            script = os.path.join(BAKER_DIR, "setup.sh")
            run_shell_screen(stdscr, "Full Setup", ["bash", script], sudo=True)
        elif idx == 1:
            screen_hdmi(stdscr)
        elif idx == 2:
            run_shell_screen(stdscr, "Update System",
                             ["sudo", "apt", "update", "-y"])
        elif idx == 3:
            run_shell_screen(stdscr, "Install mpv",
                             ["sudo", "apt", "install", "-y", "mpv"])
        elif idx == 4:
            run_shell_screen(stdscr, "Install Flask",
                             ["pip3", "install", "flask"])


def screen_hdmi(stdscr):
    config_paths = ["/boot/firmware/config.txt", "/boot/config.txt"]
    config_file = None
    for p in config_paths:
        if os.path.exists(p):
            config_file = p
            break

    recommended = [
        "hdmi_force_hotplug=1",
        "hdmi_group=1",
        "hdmi_mode=16",
        "dtparam=audio=on",
    ]

    lines = [
        f"Config file: {config_file or 'NOT FOUND'}",
        "",
        "Recommended settings for TV (1080p 60Hz):",
        "",
    ] + [f"  {r}" for r in recommended]

    if config_file:
        lines += [
            "",
            "Select 'Apply' below to add missing lines to config.txt",
        ]

    items = []
    if config_file:
        items.append("Apply HDMI Settings to config.txt")
    items.append("Show Current config.txt")

    while True:
        idx = pick_menu(stdscr, "HDMI Optimization", items,
                        subtitle="TV 1080p 60Hz settings")
        if idx == -1:
            return
        label = items[idx]
        if label.startswith("Apply"):
            curses.endwin()
            print("\nApplying HDMI settings...\n")
            try:
                with open(config_file, "r") as f:
                    existing = f.read()
                added = []
                with open(config_file, "a") as f:
                    for r in recommended:
                        key = r.split("=")[0]
                        if key not in existing:
                            f.write(f"\n{r}")
                            added.append(r)
                if added:
                    print(f"Added: {added}")
                else:
                    print("All settings already present.")
            except PermissionError:
                print("Permission denied — re-run: sudo python3 power.py")
            print("\nPress Enter to continue...")
            input()
            stdscr.refresh()
            setup_colors()
        elif label.startswith("Show"):
            if config_file:
                run_shell_screen(stdscr, "config.txt", ["cat", config_file])


def screen_power_options(stdscr):
    items = [
        "Reboot Pi",
        "Shutdown Pi",
        "Restart Baker Menu",
    ]
    idx = pick_menu(stdscr, "Power Options", items)
    if idx == -1:
        return
    if idx == 0:
        curses.endwin()
        os.system("sudo reboot")
    elif idx == 1:
        curses.endwin()
        os.system("sudo shutdown -h now")
    elif idx == 2:
        raise SystemExit("restart")


# ──────────────────────────────────────────────────────────────
# Main Menu
# ──────────────────────────────────────────────────────────────

MAIN_ITEMS = [
    ("[GAME]  Launch Game",          screen_launch_game),
    ("[FILM]  Daily Watcher",        screen_daily_watcher),
    ("[WEB ]  Filmmaker Web Hub",    screen_web_hub),
    ("[CTRL]  Controller Setup",     screen_controllers),
    ("[SETUP] System Setup",         screen_setup),
    ("[INFO]  System Diagnostics",   screen_diagnostics),
    ("[PWR ]  Power Options",        screen_power_options),
]


def main(stdscr):
    curses.curs_set(0)
    setup_colors()

    temp = get_cpu_temp()
    model = get_pi_model()
    subtitle = f"{model}   |   Temp: {temp}   |   IP: {get_ip()}"

    labels = [item[0] for item in MAIN_ITEMS]

    while True:
        idx = pick_menu(stdscr, "Main Menu", labels,
                        subtitle=subtitle,
                        back_label="[EXIT]  Exit Baker")
        if idx == -1:
            break
        fn = MAIN_ITEMS[idx][1]
        fn(stdscr)


def run():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except SystemExit as e:
        if str(e) == "restart":
            os.execv(sys.executable, [sys.executable] + sys.argv)
    print("\nBaker menu closed.\n")


if __name__ == "__main__":
    run()
