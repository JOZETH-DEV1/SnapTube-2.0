from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import threading
import json

app = Flask(__name__)

DOWNLOAD_DIR = "/storage/emulated/0/Download/Musica"
if not os.path.exists(DOWNLOAD_DIR):
    try:
        os.makedirs(DOWNLOAD_DIR)
    except:
        DOWNLOAD_DIR = "downloads"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TEMP_DIR = "temp_dl"
os.makedirs(TEMP_DIR, exist_ok=True)

PLAYLISTS_FILE = "playlists.json"

def load_playlists():
    if not os.path.exists(PLAYLISTS_FILE):
        return {}
    try:
        with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_playlists(data):
    with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

downloads_progress = {}

def get_downloaded_files():
    try:
        return [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]
    except:
        return []

class MyLogger:
    def __init__(self, video_id):
        self.video_id = video_id
    def debug(self, msg):
        if "[download]" in msg and "%" in msg:
            try:
                percent = msg.split("%")[0].split()[-1]
                downloads_progress[self.video_id] = float(percent)
            except: pass
    def warning(self, msg): pass
    def error(self, msg): pass

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': True,
        'quiet': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch100:{query}", download=False)
            if 'entries' in result:
                videos = []
                downloaded_files = get_downloaded_files()
                downloaded_basenames = [os.path.splitext(f)[0].lower() for f in downloaded_files]
                
                for entry in result['entries']:
                    title = entry.get('title', '')
                    safe_title = title.replace('/', '_').replace('\\', '_').replace(':', ' -').replace('"', "'")
                    is_downloaded = safe_title.lower() in downloaded_basenames
                    
                    videos.append({
                        'id': entry.get('id'),
                        'title': title,
                        'channel': entry.get('uploader'),
                        'duration': entry.get('duration'),
                        'url': entry.get('url'),
                        'is_downloaded': is_downloaded
                    })
                return jsonify(videos)
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/stream")
def stream():
    video_id = request.args.get("id")
    audio_only = request.args.get("audio_only", "true") == "true"
    
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
        
    ydl_opts = {
        'format': 'bestaudio/best' if audio_only else 'best[ext=mp4]/best',
        'quiet': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return jsonify({
                "url": info['url'],
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "channel": info.get('uploader')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_download(video_id, url, dl_type="audio", quality="720"):
    downloads_progress[video_id] = 0.0
    
    if dl_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'paths': {'home': DOWNLOAD_DIR, 'temp': TEMP_DIR},
            'outtmpl': {'default': '%(title)s.%(ext)s'},
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'nocheckcertificate': True,
            'quiet': False,
            'logger': MyLogger(video_id)
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'paths': {'home': DOWNLOAD_DIR, 'temp': TEMP_DIR},
            'outtmpl': {'default': '%(title)s.%(ext)s'},
            'merge_output_format': 'mp4',
            'nocheckcertificate': True,
            'quiet': False,
            'logger': MyLogger(video_id)
        }
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        downloads_progress[video_id] = 100.0
    except Exception as e:
        downloads_progress[video_id] = -1.0

@app.route("/api/download", methods=["POST"])
def download():
    data = request.json
    video_id = data.get("id")
    url = data.get("url")
    dl_type = data.get("type", "audio")
    quality = data.get("quality", "720")
    
    if not video_id or not url: return jsonify({"error": "Missing params"}), 400
    if "youtube.com" not in url and "youtu.be" not in url: url = f"https://www.youtube.com/watch?v={video_id}"
    
    threading.Thread(target=run_download, args=(video_id, url, dl_type, quality)).start()
    return jsonify({"status": "started", "id": video_id})

@app.route("/api/progress")
def progress():
    return jsonify(downloads_progress)

# --- PLAYLISTS API ---

@app.route("/api/playlists", methods=["GET"])
def get_playlists():
    return jsonify(load_playlists())

@app.route("/api/playlists", methods=["POST"])
def create_playlist():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name required"}), 400
    
    pl = load_playlists()
    if name not in pl:
        pl[name] = []
        save_playlists(pl)
    return jsonify(pl)

@app.route("/api/playlists/<playlist_name>/add", methods=["POST"])
def add_to_playlist(playlist_name):
    song = request.json
    pl = load_playlists()
    if playlist_name not in pl:
        return jsonify({"error": "Playlist not found"}), 404
        
    # Evitar duplicados exactos por ID
    if not any(s.get("id") == song.get("id") for s in pl[playlist_name]):
        pl[playlist_name].append(song)
        save_playlists(pl)
        
    return jsonify(pl)

@app.route("/api/playlists/<playlist_name>/remove", methods=["POST"])
def remove_from_playlist(playlist_name):
    video_id = request.json.get("id")
    pl = load_playlists()
    if playlist_name in pl:
        pl[playlist_name] = [s for s in pl[playlist_name] if s.get("id") != video_id]
        save_playlists(pl)
    return jsonify(pl)

@app.route("/api/playlists/<playlist_name>", methods=["DELETE"])
def delete_playlist(playlist_name):
    pl = load_playlists()
    if playlist_name in pl:
        del pl[playlist_name]
        save_playlists(pl)
    return jsonify(pl)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
