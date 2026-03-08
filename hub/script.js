const state = {
    focusIndex: 0,
    currentView: 'menu', // or 'dailies'
    focusElements: [],
    gamepadConnected: false,
    lastButtonPress: 0
};

// --- Initialization ---

window.addEventListener("DOMContentLoaded", () => {
    updateClock();
    setInterval(updateClock, 1000);
    refreshFocusElements();
    
    window.addEventListener("gamepadconnected", () => {
        state.gamepadConnected = true;
        document.getElementById('controller-status').innerText = "Controller Connected";
        document.getElementById('controller-status').className = "connected";
    });

    window.addEventListener("gamepaddisconnected", () => {
        state.gamepadConnected = false;
        document.getElementById('controller-status').innerText = "No Controller";
        document.getElementById('controller-status').className = "disconnected";
    });

    requestAnimationFrame(gamepadLoop);
});

function updateClock() {
    const now = new Date();
    document.getElementById('clock').innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// --- Navigation Logic ---

function refreshFocusElements() {
    const selector = state.currentView === 'menu' ? '#menu .focusable' : '#dailies-view .focusable';
    state.focusElements = Array.from(document.querySelectorAll(selector));
    updateFocus();
}

function updateFocus() {
    state.focusElements.forEach((el, i) => {
        el.classList.toggle('focused', i === state.focusIndex);
    });
}

function moveFocus(dir) {
    state.focusIndex = (state.focusIndex + dir + state.focusElements.length) % state.focusElements.length;
    updateFocus();
}

function handleConfirm() {
    const focused = state.focusElements[state.focusIndex];
    if (!focused) return;

    if (state.currentView === 'menu') {
        const action = focused.dataset.action;
        if (action === 'launch-game') launchGame();
        if (action === 'view-dailies') showDailies();
        if (action === 'system') alert("Shutdown available in Settings");
    } else if (state.currentView === 'dailies') {
        if (focused.classList.contains('back-btn')) {
            showMenu();
        } else {
            playVideo(focused.dataset.url, focused.querySelector('h3').innerText);
        }
    }
}

// --- API Interactions ---

function launchGame() {
    fetch('/api/launch', { method: 'POST' })
        .then(r => r.json())
        .then(data => console.log(data));
}

function showDailies() {
    state.currentView = 'dailies';
    document.getElementById('menu').classList.add('hidden');
    document.getElementById('dailies-view').classList.remove('hidden');
    
    fetch('/api/dailies')
        .then(r => r.json())
        .then(videos => {
            const grid = document.getElementById('video-grid');
            grid.innerHTML = '';
            videos.forEach(v => {
                const card = document.createElement('div');
                card.className = 'card focusable';
                card.dataset.url = `/api/play/${v.path}`;
                card.innerHTML = `<h3>${v.name}</h3><p>${(v.size / (1024*1024)).toFixed(1)} MB</p>`;
                grid.appendChild(card);
            });
            state.focusIndex = 0;
            refreshFocusElements();
        });
}

function showMenu() {
    state.currentView = 'menu';
    document.getElementById('menu').classList.remove('hidden');
    document.getElementById('dailies-view').classList.add('hidden');
    state.focusIndex = 0;
    refreshFocusElements();
}

function playVideo(url, name) {
    const overlay = document.getElementById('video-overlay');
    const player = document.getElementById('player');
    const title = document.getElementById('video-title');
    
    title.innerText = name;
    player.src = url;
    overlay.classList.remove('hidden');
    player.play();
}

function closeVideo() {
    const overlay = document.getElementById('video-overlay');
    const player = document.getElementById('player');
    player.pause();
    overlay.classList.add('hidden');
}

// --- Gamepad Loop ---

function gamepadLoop() {
    const gamepads = navigator.getGamepads();
    if (!gamepads[0]) {
        requestAnimationFrame(gamepadLoop);
        return;
    }

    const gp = gamepads[0];
    const now = Date.now();

    if (now - state.lastButtonPress > 200) {
        // D-Pad or Left Stick
        if (gp.axes[0] > 0.5 || gp.buttons[15].pressed) moveFocus(1);
        if (gp.axes[0] < -0.5 || gp.buttons[14].pressed) moveFocus(-1);
        
        // A Button (South)
        if (gp.buttons[0].pressed) {
            handleConfirm();
            state.lastButtonPress = now;
        }

        // B Button (East) - Close video
        if (gp.buttons[1].pressed) {
            closeVideo();
            state.lastButtonPress = now;
        }
    }

    requestAnimationFrame(gamepadLoop);
}
