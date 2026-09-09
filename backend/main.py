import os
import tempfile
import urllib.request
import urllib.error
import yt_dlp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

# ==========================================
# CORS Middleware
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Frontend Routes
# ==========================================

@app.api_route("/index", methods=["GET", "HEAD"])
@app.api_route("/index.html", methods=["GET", "HEAD"])
@app.api_route("/single", methods=["GET", "HEAD"])
def get_index():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return FileResponse("frontend/display.html")

@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/display", methods=["GET", "HEAD"])
@app.api_route("/display.html", methods=["GET", "HEAD"])
def get_display():
    return FileResponse("frontend/display.html")

@app.api_route("/remote", methods=["GET", "HEAD"])
@app.api_route("/controller", methods=["GET", "HEAD"])
@app.api_route("/controller.html", methods=["GET", "HEAD"])
def get_controller():
    return FileResponse("frontend/controller.html")

# ==========================================
# API Search
# ==========================================

@app.get("/api/search")
def api_search(q: str = ""):
    if not q.strip():
        return {"success": True, "results": []}
    
    try:
        raw_results = search_youtube_karaoke(q)
        formatted_results = []
        for item in raw_results:
            vid = item.get("videoId") or item.get("id")
            if not vid:
                continue
                
            formatted_results.append({
                "id": vid,
                "videoId": vid,
                "title": item.get("title", "ไม่ทราบชื่อเพลง"),
                "thumbnail": item.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
                "channel": item.get("channel") or item.get("uploader") or "YouTube",
                "duration": item.get("duration", "")
            })
            
        return {"success": True, "results": formatted_results}
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}

# ==========================================
# API Stream Proxy
# ==========================================

@app.get("/api/stream")
def api_stream(id: str = "", play: str = "", request: Request = None):
    """
    แก้พารามิเตอร์ play เป็น str เพื่อให้รองรับทั้ง true, 1, yes
    และป้องกัน FastAPI / Pydantic แจ้งเตือน Error bool_parsing
    """
    if not id.strip():
        return {"success": False, "error": "Missing video ID"}

    # ตรวจจับว่าผู้ใช้ต้องการสตรีมตรงหรือไม่
    is_play = str(play).lower() in ["true", "1", "yes"]
    range_header = request.headers.get("range") if request else None

    if is_play or range_header:
        return stream_video_content(id, request)

    base_url = str(request.base_url).rstrip("/") if request else ""
    return {
        "success": True,
        "url": f"{base_url}/api/stream?id={id}&play=true"
    }

def get_cookie_file_path():
    """จัดการไฟล์คุกกี้จาก Environment Variable หรือไฟล์ในโฟลเดอร์"""
    cookie_env = os.environ.get("YOUTUBE_COOKIES", "").strip()
    if cookie_env:
        temp_dir = tempfile.gettempdir()
        cookie_path = os.path.join(temp_dir, "yt_cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookie_env)
        return cookie_path

    if os.path.exists("cookies.txt"):
        return "cookies.txt"
    if os.path.exists("backend/cookies.txt"):
        return "backend/cookies.txt"
    return None

def stream_video_content(video_id: str, request: Request):
    ydl_opts = {
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb"]
            }
        },
        "format": "18/22/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": False,
    }

    cookie_file = get_cookie_file_path()
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            if not info:
                raise HTTPException(status_code=404, detail="Video not found")

            if "entries" in info:
                info = info["entries"][0]

            video_url = info.get("url")
            if not video_url:
                raise HTTPException(status_code=500, detail="Cannot extract video stream URL")

            ext = info.get("ext", "mp4")
            mime_type = f"video/{ext}"

            headers = dict(info.get("http_headers", {}))
            
            # รองรับ Range Header จากแท็บเล็ต/ทีวี
            client_range = request.headers.get("range") if request else None
            if client_range:
                headers["Range"] = client_range

            req = urllib.request.Request(video_url, headers=headers)
            
            try:
                response = urllib.request.urlopen(req, timeout=25)
            except urllib.error.HTTPError as err:
                raise HTTPException(status_code=err.code, detail=f"YouTube upstream error: {err.reason}")

            status_code = response.status
            content_range = response.headers.get("Content-Range")
            content_length = response.headers.get("Content-Length")

            resp_headers = {
                "Accept-Ranges": "bytes",
                "Content-Type": response.headers.get("Content-Type", mime_type),
                "Cache-Control": "no-cache",
            }
            if content_range:
                resp_headers["Content-Range"] = content_range
            if content_length:
                resp_headers["Content-Length"] = content_length

            def iterfile():
                try:
                    while True:
                        chunk = response.read(128 * 1024)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    response.close()

            return StreamingResponse(
                iterfile(),
                status_code=status_code,
                media_type=resp_headers["Content-Type"],
                headers=resp_headers
            )

    except Exception as e:
        print(f"[STREAM ERROR] video_id={video_id} error={e}")
        raise HTTPException(status_code=500, detail=str(e))
