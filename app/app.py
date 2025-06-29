import os
import signal
import subprocess
import threading
import time
import requests
import json
import platform
from flask import Flask, request, render_template_string, jsonify
import re

app = Flask(__name__)
print("*** app.py started")

# Environment variables
CDVR_HOST = os.getenv("CDVR_HOST", "192.168.1.152")
CDVR_PORT = int(os.getenv("CDVR_PORT", "8089"))
CDVR_CHNLNUM = os.getenv("CDVR_CHNLNUM", "280")
RTP_HOST = os.getenv("RTP_HOST", "127.0.0.1")
RTP_PORT = str(os.getenv("RTP_PORT", "4444"))
OUTPUT_FPS = str(os.getenv("OUTPUT_FPS", "60"))
CHECK_INTERVAL_SECONDS = 60
STREAM_PROCESS = None
CURRENT_VLC_PROCESS_ID = None
KILL_COUNTDOWN_MINUTES = 6
CHANNELS = []
FAVORITES = []
FAVORITES_FILE = "/app/data/favorites.json"

def load_favorites():
    """Load favorite channels from JSON file."""
    global FAVORITES
    try:
        if os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, 'r') as f:
                FAVORITES = json.load(f)
            print(f"*** Favorites loaded: {len(FAVORITES)} from {FAVORITES_FILE}")
        else:
            print(f"*** No favorites file at {FAVORITES_FILE}")
    except Exception as e:
        print(f"*** Error loading favorites: {e}")

def save_favorites():
    """Save favorite channels to JSON file."""
    try:
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(FAVORITES, f, indent=2)
        print(f"*** Favorites saved: {len(FAVORITES)} to {FAVORITES_FILE}")
    except Exception as e:
        print(f"*** Error saving favorites: {e}")

load_favorites()

def scrape_m3u():
    """Scrape channel list from Channels DVR M3U."""
    global CHANNELS
    try:
        m3u_url = f"http://{CDVR_HOST}:{CDVR_PORT}/devices/ANY/channels.m3u"
        response = requests.get(m3u_url, timeout=5)
        if response.status_code == 200:
            lines = response.text.splitlines()
            channels = []
            current_channel = {}
            for line in lines:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    tvg_chno_match = re.search(r'tvg-chno="([^"]+)"', line)
                    tvg_name_match = re.search(r'tvg-name="([^"]+)"', line)
                    name_match = re.search(r',([^,]+)$', line)
                    if tvg_chno_match:
                        current_channel['number'] = tvg_chno_match.group(1)
                    if tvg_name_match:
                        current_channel['name'] = tvg_name_match.group(1)
                    elif name_match:
                        current_channel['name'] = name_match.group(1).strip()
                elif line.startswith('http://'):
                    if current_channel.get('number') and current_channel.get('name'):
                        channels.append({
                            'number': current_channel['number'],
                            'name': current_channel['name']
                        })
                    current_channel = {}
            CHANNELS = channels
            print(f"*** Channels loaded: {len(CHANNELS)} from M3U")
        else:
            print(f"*** Failed to fetch M3U: Status {response.status_code}")
    except Exception as e:
        print(f"*** Error scraping M3U: {e}")

scrape_m3u()

def detect_qsv():
    """Detect if Intel QuickSync Video (QSV) is available."""
    try:
        if not os.path.exists("/dev/dri"):
            print("*** No /dev/dri found, QSV unavailable")
            return False
        result = subprocess.run(["which", "vainfo"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("*** vainfo not found, QSV unavailable")
            return False
        result = subprocess.run(["vainfo"], capture_output=True, text=True, check=False)
        if result.returncode == 0 and "VAEntrypointEncSlice" in result.stdout and "H.264" in result.stdout:
            print("*** Intel QuickSync H.264 encoding detected")
            return True
        print("*** vainfo failed or no QSV H.264 support")
        return False
    except Exception as e:
        print(f"*** Error detecting QSV: {e}")
        return False

# Set video codec: use mp4v for arm64, otherwise check for QSV
VIDEO_CODEC = "mp4v" if platform.machine() == "arm64" else ("h264_vaapi" if detect_qsv() else "mp4v")
print(f"*** Using video codec: {VIDEO_CODEC}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Multi4Channels</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            background: #111;
            color: white;
            margin: 0;
            overflow-x: hidden;
        }
        header {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0.5em 1em;
            background: #222;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 10;
        }
        h1 {
            font-size: 1.8em;
            margin: 0;
            text-align: center;
        }
        .hamburger {
            font-size: 1.8em;
            cursor: pointer;
            padding: 0.8em;
            position: absolute;
            right: 0.5em;
            text-overflow: clip;
            white-space: nowrap;
            z-index: 11;
        }
        #menu {
            position: fixed;
            top: 0;
            right: 0;
            width: 70%;
            max-width: 250px;
            height: 100%;
            background: #222;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            padding-top: 4em;
            z-index: 9;
        }
        #menu.open {
            transform: translateX(0);
        }
        #menu ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        #menu li {
            padding: 1em 1.5em;
            border-bottom: 1px solid #444;
            font-size: 1.1em;
            cursor: pointer;
        }
        #menu li:hover {
            background: #333;
        }
        .container {
            padding: 4.5em 1em 1em;
            max-width: 600px;
            margin: 0 auto;
        }
        form {
            text-align: center;
        }
        input[type=text] {
            font-size: 1.5em;
            width: 4.5em;
            margin: 0.3em;
            padding: 0.2em;
            box-sizing: border-box;
            border-radius: 4px;
        }
        .grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.3em;
        }
        .grid div {
            width: 48%;
            min-width: 100px;
        }
        input[type=submit] {
            font-size: 1.1em;
            padding: 0.6em 1.2em;
            margin: 1em 0;
            cursor: pointer;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
        }
        input[type=submit]:hover {
            background: #0056b3;
        }
        #favorites {
            margin-top: 1.5em;
            text-align: center;
        }
        #favorites h2 {
            font-size: 1.3em;
            margin: 0.5em 0;
        }
        #favorites ul {
            list-style: none;
            padding: 0;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5em;
        }
        #favorites li {
            font-size: 0.95em;
            padding: 0.6em;
            background: #333;
            margin: 0.3em;
            border-radius: 4px;
            cursor: pointer;
        }
        #favorites li:hover {
            background: #444;
        }
        #channels-page {
            display: none;
            padding: 4.5em 1em 1em;
            max-width: 600px;
            margin: 0 auto;
        }
        #channels-page h2 {
            font-size: 1.3em;
            margin: 0.5em 0;
        }
        #channels-page ul {
            list-style: none;
            padding: 0;
        }
        #channels-page li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6em;
            background: #333;
            margin: 0.3em 0;
            border-radius: 4px;
            font-size: 0.95em;
        }
        .heart {
            cursor: pointer;
            font-size: 1.2em;
            padding: 0.3em;
        }
        .heart.favorited {
            color: red;
        }
        .button-group {
            text-align: center;
            margin-top: 1em;
        }
        .button-group button.save {
            font-size: 1.1em;
            padding: 0.6em 1.2em;
            margin: 0.5em;
            cursor: pointer;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
        }
        .button-group button.save:hover {
            background: #c82333;
        }
        .button-group button.back {
            font-size: 1.1em;
            padding: 0.6em 1.2em;
            margin: 0.5em;
            cursor: pointer;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
        }
        .button-group button.back:hover {
            background: #0056b3;
        }
        #notification {
            display: none;
            position: fixed;
            top: 50%;
            left: 50establishment
            transform: translate(-50%, -50%);
            background: #333;
            padding: 1em 2em;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            z-index: 1000;
            text-align: center;
        }
        #notification p {
            font-size: 0.95em;
            margin: 0 0 1em;
        }
        #notification button {
            font-size: 1em;
            padding: 0.5em 1em;
            cursor: pointer;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
        }
        #notification button:hover {
            background: #0056b3;
        }
        @media (min-width: 600px) {
            h1 {
                font-size: 2.2em;
            }
            input[type=text] {
                font-size: 1.8em;
            }
            input[type=submit] {
                font-size: 1.2em;
            }
            #menu li {
                font-size: 1.2em;
            }
            #favorites ul {
                gap: 1em;
            }
        }
        @media (max-width: 360px) {
            .grid div {
                width: 100%;
            }
            .hamburger {
                padding: 0.5em;
                right: 0.2em;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>Multi4Channels</h1>
        <div class="hamburger">☰</div>
    </header>
    <div id="menu">
        <ul>
            <li onclick="reloadM3U()">Reload M3U from Channels</li>
            <li onclick="showChannels()">Available Channels</li>
            <li onclick="closeStream()">Close Current Stream</li>
            <li onclick="goHome()">Home</li>
        </ul>
    </div>
    <div class="container">
        <form method="post" action="/start" id="stream-form">
            <div class="grid">
                <div><input name="ch1" type="text" placeholder="Ch1" required inputmode="decimal"></div>
                <div><input name="ch2" type="text" placeholder="Ch2" required inputmode="decimal"></div>
                <div><input name="ch3" type="text" placeholder="Ch3" inputmode="decimal"></div>
                <div><input name="ch4" type="text" placeholder="Ch4" inputmode="decimal"></div>
            </div>
            <input type="submit" value="Start Stream">
        </form>
        <div id="favorites">
            <h2>Favorites</h2>
            <ul id="favorites-list"></ul>
        </div>
    </div>
    <div id="channels-page">
        <h2>Available Channels</h2>
        <ul id="channels-list"></ul>
        <div class="button-group">
            <button class="save" onclick="saveFavorites()">Save</button>
            <button class="back" onclick="goHome()">Go Back</button>
        </div>
    </div>
    <div id="notification">
        <p id="notification-text">Stream started</p>
        <button onclick="dismissNotification()">Dismiss</button>
    </div>

    <script>
        const menu = document.getElementById('menu');
        const hamburger = document.querySelector('.hamburger');
        const channelsPage = document.getElementById('channels-page');
        const mainContainer = document.querySelector('.container');
        const notification = document.getElementById('notification');
        const notificationText = document.getElementById('notification-text');
        const streamForm = document.getElementById('stream-form');

        hamburger.addEventListener('click', () => {
            menu.classList.toggle('open');
        });

        document.addEventListener('click', e => {
            if (!menu.contains(e.target) && !hamburger.contains(e.target)) {
                menu.classList.remove('open');
            }
        });

        function reloadM3U() {
            fetch('/reload_m3u')
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    menu.classList.remove('open');
                });
        }

        function showChannels() {
            fetch('/channels')
                .then(response => response.json())
                .then(data => {
                    const channelsList = document.getElementById('channels-list');
                    channelsList.innerHTML = '';
                    data.channels.forEach(channel => {
                        const li = document.createElement('li');
                        const isFavorited = data.favorites.some(fav => fav.number === channel.number);
                        li.innerHTML = `
                            ${channel.name} (${channel.number})
                            <span class="heart ${isFavorited ? 'favorited' : ''}" data-number="${channel.number}" data-name="${channel.name}">${isFavorited ? '♥' : '♡'}</span>
                        `;
                        channelsList.appendChild(li);
                    });
                    mainContainer.style.display = 'none';
                    channelsPage.style.display = 'block';
                    menu.classList.remove('open');
                    attachHeartListeners();
                });
        }

        function closeStream() {
            fetch('/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    notificationText.textContent = data.message;
                    notification.style.display = 'block';
                    setTimeout(() => {
                        notification.style.display = 'none';
                    }, 3000);
                    menu.classList.remove('open');
                });
        }

        function goHome() {
            channelsPage.style.display = 'none';
            mainContainer.style.display = 'block';
            menu.classList.remove('open');
        }

        function saveFavorites() {
            fetch('/save_favorites')
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                });
        }

        function dismissNotification() {
            notification.style.display = 'none';
        }

        function attachHeartListeners() {
            document.querySelectorAll('.heart').forEach(heart => {
                heart.addEventListener('click', () => {
                    const number = heart.dataset.number;
                    const name = heart.dataset.name;
                    fetch('/toggle_favorite', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ number, name })
                    })
                    .then(response => response.json())
                    .then(data => {
                        heart.classList.toggle('favorited');
                        heart.textContent = heart.classList.contains('favorited') ? '♥' : '♡';
                        updateFavoritesList(data.favorites);
                    });
                });
            });
        }

        function updateFavoritesList(favorites) {
            const favoritesList = document.getElementById('favorites-list');
            favoritesList.innerHTML = '';
            favorites.forEach(fav => {
                const li = document.createElement('li');
                li.textContent = `${fav.name} (${fav.number})`;
                li.dataset.number = fav.number;
                li.addEventListener('click', () => {
                    const inputs = document.querySelectorAll('input[name^="ch"]');
                    for (let input of inputs) {
                        if (!input.value) {
                            input.value = fav.number;
                            break;
                        }
                    }
                });
                favoritesList.appendChild(li);
            });
        }

        fetch('/channels')
            .then(response => response.json())
            .then(data => updateFavoritesList(data.favorites));

        streamForm.addEventListener('submit', e => {
            e.preventDefault();
           ним
            fetch('/start', {
                method: 'POST',
                body: new FormData(streamForm)
            })
            .then(response => response.text())
            .then(() => {
                notificationText.textContent = 'Stream started';
                notification.style.display = 'block';
                setTimeout(() => {
                    notification.style.display = 'none';
                }, 5000);
            });
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/start", methods=["POST"])
def start_stream():
    global STREAM_PROCESS, CURRENT_VLC_PROCESS_ID

    ch1 = request.form.get("ch1")
    ch2 = request.form.get("ch2")
    ch3 = request.form.get("ch3")
    ch4 = request.form.get("ch4")
    channels = [ch for ch in [ch1, ch2, ch3, ch4] if ch]

    print(f"*** Starting stream with channels: {', '.join(channels)}")

    if CURRENT_VLC_PROCESS_ID and STREAM_PROCESS:
        try:
            print(f"*** Terminating VLC process PID {CURRENT_VLC_PROCESS_ID}")
            os.kill(CURRENT_VLC_PROCESS_ID, signal.SIGTERM)
            STREAM_PROCESS.wait(timeout=5)
            print(f"*** VLC process PID {CURRENT_VLC_PROCESS_ID} terminated")
        except ProcessLookupError:
            print("*** Previous VLC process already terminated")
        except subprocess.TimeoutExpired:
            print(f"*** VLC process PID {CURRENT_VLC_PROCESS_ID} did not terminate gracefully, forcing kill")
            os.kill(CURRENT_VLC_PROCESS_ID, signal.SIGKILL)
            STREAM_PROCESS.wait(timeout=2)
        except Exception as e:
            print(f"*** Error terminating VLC process: {e}")
        CURRENT_VLC_PROCESS_ID = None
        STREAM_PROCESS = None
        time.sleep(1)

    with open("/tmp/multi4.vlm", "w") as f:
        f.write("del all\n\n")
        for i, ch in enumerate(channels):
            f.write(f"new ch{i+1} broadcast enabled\n")
            f.write(f"setup ch{i+1} input http://{CDVR_HOST}:{CDVR_PORT}/devices/ANY/channels/{ch}/stream.mpg\n")
            f.write(f"setup ch{i+1} option http-reconnect\n")
            f.write(f"setup ch{i+1} option network-caching=1000\n")
            if i == 1:
                f.write(f"setup ch{i+1} output #duplicate{{dst=mosaic-bridge{{id=ch{i+1},width=960,height=540}},select=video,dst=bridge-out{{id=0}},select=audio}}\n\n")
            else:
                f.write(f"setup ch{i+1} output #mosaic-bridge{{id=ch{i+1},width=960,height=540}}\n\n")

        f.write("new bg broadcast enabled\n")
        f.write("setup bg input /app/photos/bg.jpg\n")
        f.write("setup bg option image-duration=-1\n")
        f.write("setup bg option image-fps=60/1\n")
        f.write(
            f'setup bg output #transcode{{vcodec={VIDEO_CODEC},vb=0,fps={OUTPUT_FPS},acodec=none,channels=2,sfilter=mosaic{{alpha=255,width=1920,height=1080,cols=2,rows=2,position=1,order="ch1,ch2,ch3,ch4",keep-aspect-ratio=enabled,mosaic-align=0,keep-picture=1}}}}:bridge-in{{offset=100}}:rtp{{dst={RTP_HOST},port={RTP_PORT},mux=ts,sap,name=Multi4,ttl=10}}\n\n'
        )
        f.write("control bg play\n")
        for i in range(len(channels)):
            f.write(f"control ch{i+1} play\n")

    try:
        STREAM_PROCESS = subprocess.Popen([
            "cvlc", "--vlm-conf", "/tmp/multi4.vlm",
            "--verbose", "1", "--file-logging", "--logfile", "/tmp/vlc.log",
            "--network-caching=1000", "--sout-mux-caching=1000"
        ])
        CURRENT_VLC_PROCESS_ID = STREAM_PROCESS.pid
        print(f"*** VLC started with PID {CURRENT_VLC_PROCESS_ID}")
    except Exception as e:
        print(f"*** Error starting VLC process: {e}")
        return "Failed to start stream", 500

    if CDVR_CHNLNUM:
        threading.Thread(target=watch_for_quit, daemon=True).start()

    return "Stream started"

@app.route("/stop", methods=["POST"])
def stop_stream():
    global STREAM_PROCESS, CURRENT_VLC_PROCESS_ID

    if CURRENT_VLC_PROCESS_ID and STREAM_PROCESS:
        try:
            print(f"*** Stopping VLC process PID {CURRENT_VLC_PROCESS_ID}")
            os.kill(CURRENT_VLC_PROCESS_ID, signal.SIGTERM)
            STREAM_PROCESS.wait(timeout=5)
            print(f"*** VLC process PID {CURRENT_VLC_PROCESS_ID} stopped")
        except ProcessLookupError:
            print("*** VLC process already stopped")
        except subprocess.TimeoutExpired:
            print(f"*** VLC process PID {CURRENT_VLC_PROCESS_ID} did not stop gracefully, forcing kill")
            os.kill(CURRENT_VLC_PROCESS_ID, signal.SIGKILL)
            STREAM_PROCESS.wait(timeout=2)
        except Exception as e:
            print(f"*** Error stopping VLC process: {e}")
        CURRENT_VLC_PROCESS_ID = None
        STREAM_PROCESS = None
        return jsonify({"message": "Stream closed successfully"})
    else:
        return jsonify({"message": "No stream is running"})

@app.route("/reload_m3u")
def reload_m3u():
    scrape_m3u()
    return jsonify({"message": "M3U playlist reloaded successfully"})

@app.route("/channels")
def get_channels():
    return jsonify({"channels": CHANNELS, "favorites": FAVORITES})

@app.route("/toggle_favorite", methods=["POST"])
def toggle_favorite():
    global FAVORITES
    data = request.get_json()
    channel = {"number": data["number"], "name": data["name"]}
    if channel in FAVORITES:
        FAVORITES.remove(channel)
    else:
        FAVORITES.append(channel)
    save_favorites()
    return jsonify({"favorites": FAVORITES})

@app.route("/save_favorites", methods=["GET"])
def save_favorites_endpoint():
    save_favorites()
    return jsonify({"message": "Favorites saved successfully"})

def watch_for_quit():
    global CURRENT_VLC_PROCESS_ID
    inactive_minutes = 0
    print(f"*** Monitoring activity on channel {CDVR_CHNLNUM}")

    while True:
        try:
            r = requests.get(f"http://{CDVR_HOST}:{CDVR_PORT}/dvr", timeout=5)
            if r.status_code == 200:
                if f"ch{CDVR_CHNLNUM}".lower() in r.text.lower():
                    print(f"*** Channel {CDVR_CHNLNUM} still being watched")
                    inactive_minutes = 0
                else:
                    inactive_minutes += 1
                    print(f"*** Channel no longer being watched. Countdown to kill: {inactive_minutes} / {KILL_COUNTDOWN_MINUTES} min")
                    if inactive_minutes >= KILL_COUNTDOWN_MINUTES:
                        if CURRENT_VLC_PROCESS_ID:
                            try:
                                os.kill(CURRENT_VLC_PROCESS_ID, signal.SIGKILL)
                                print(f"*** Killed VLC process PID {CURRENT_VLC_PROCESS_ID}")
                            except Exception as e:
                                print(f"*** Error killing VLC: {e}")
                            CURRENT_VLC_PROCESS_ID = None
                        return
        except Exception as e:
            print(f"*** Error checking DVR activity: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    print("*** Starting Flask app")
    web_page_port = int(os.getenv("WEB_PAGE_PORT", "9799"))
    app.run(host="0.0.0.0", port=web_page_port)
