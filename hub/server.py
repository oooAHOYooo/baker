import os
import subprocess
from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__, static_folder='.')

# --- CONFIGURATION ---
# Default to /media/pi to find USB drives, or fall back to a local 'dailies' folder
DAILIES_DIR = os.environ.get('DAILIES_DIR', '/media/pi')
if not os.path.exists(DAILIES_DIR):
    DAILIES_DIR = os.path.join(os.path.dirname(__file__), 'dailies')
    os.makedirs(DAILIES_DIR, exist_ok=True)

GAME_BINARY_PATH = os.environ.get('GAME_BINARY', '/home/pi/game/my_game.x86_64')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/dailies')
def list_dailies():
    video_extensions = ('.mp4', '.mov', '.mkv', '.avi')
    files = []
    
    # Walk through the directory to find videos
    for root, dirs, filenames in os.walk(DAILIES_DIR):
        for f in filenames:
            if f.lower().endswith(video_extensions):
                rel_path = os.path.relpath(os.path.join(root, f), DAILIES_DIR)
                files.append({
                    'name': f,
                    'path': rel_path,
                    'size': os.path.getsize(os.path.join(root, f))
                })
    return jsonify(files)

@app.route('/api/play/<path:filename>')
def play_video(filename):
    return send_from_directory(DAILIES_DIR, filename)

@app.route('/api/launch', methods=['POST'])
def launch_game():
    try:
        # Launch game in background
        subprocess.Popen([GAME_BINARY_PATH])
        return jsonify({'status': 'success', 'message': 'Launching game...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system/shutdown', methods=['POST'])
def shutdown():
    os.system('sudo shutdown -h now')
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
