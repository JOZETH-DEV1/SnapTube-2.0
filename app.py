from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import threading

app = Flask(__name__)

# Configuración de carpeta destino
DOWNLOAD_DIR = "/storage/emulated/0/Download/Musica"
if not os.path.exists(DOWNLOAD_DIR):
    try:
        os.makedirs(DOWNLOAD_DIR)
    except:
        DOWNLOAD_DIR = "downloads" # Fallback si falla almacenamiento local
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Carpeta temporal interna para evitar bugs de FFmpeg en Android 11+
TEMP_DIR = "temp_dl"
os.makedirs(TEMP_DIR, exist_ok=True)

# Diccionario para rastrear el progreso de las descargas
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
            except:
                pass
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
            result = ydl.extract_info(f"ytsearch200:{query}", download=False)
            if 'entries' in result:
                videos = []
                downloaded_files = get_downloaded_files()
                # Remove extensions for easier matching
                downloaded_basenames = [os.path.splitext(f)[0].lower() for f in downloaded_files]
                
                for entry in result['entries']:
                    title = entry.get('title', '')
                    # Reemplazo basico que suele hacer yt-dlp con caracteres invalidos
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

def run_download(video_id, url, dl_type="audio", quality="720"):
    downloads_progress[video_id] = 0.0
    
    if dl_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'paths': {
                'home': DOWNLOAD_DIR,
                'temp': TEMP_DIR
            },
            'outtmpl': {'default': '%(title)s.%(ext)s'},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'nocheckcertificate': True,
            'quiet': False,
            'logger': MyLogger(video_id)
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'paths': {
                'home': DOWNLOAD_DIR,
                'temp': TEMP_DIR
            },
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
        print("Error en descarga:", e)
        downloads_progress[video_id] = -1.0

@app.route("/api/download", methods=["POST"])
def download():
    data = request.json
    video_id = data.get("id")
    url = data.get("url")
    dl_type = data.get("type", "audio")
    quality = data.get("quality", "720")
    
    if not video_id or not url:
        return jsonify({"error": "Missing params"}), 400
        
    if "youtube.com" not in url and "youtu.be" not in url:
        url = f"https://www.youtube.com/watch?v={video_id}"

    threading.Thread(target=run_download, args=(video_id, url, dl_type, quality)).start()
    return jsonify({"status": "started", "id": video_id})

@app.route("/api/progress")
def progress():
    return jsonify(downloads_progress)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
