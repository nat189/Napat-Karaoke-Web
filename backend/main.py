import os
import urllib.request
import yt_dlp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

# ==========================================
# เปิดใช้งาน CORS (สำคัญมาก เพื่อให้ TV/Tablet ข้ามโดเมนมาดึงสตรีมได้)
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

# 1. โหมดหน้าจอเดียว (All-in-One: index.html)
@app.api_route("/index", methods=["GET", "HEAD"])
@app.api_route("/index.html", methods=["GET", "HEAD"])
@app.api_route("/single", methods=["GET", "HEAD"])
def get_index():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return FileResponse("frontend/display.html")

# 2. โหมด 2 จอ: TV Display
@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/display", methods=["GET", "HEAD"])
@app.api_route("/display.html", methods=["GET", "HEAD"])
def get_display():
    return FileResponse("frontend/display.html")

# 3. โหมด 2 จอ: Remote Controller
@app.api_route("/remote", methods=["GET", "HEAD"])
@app.api_route("/controller", methods=["GET", "HEAD"])
@app.api_route("/controller.html", methods=["GET", "HEAD"])
def get_controller():
    return FileResponse("frontend/controller.html")

# ==========================================
# API Search (yt-dlp)
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
# API Stream (Stream Proxy ดึง Sing King ผ่าน yt-dlp)
# ==========================================

@app.get("/api/stream")
def api_stream(id: str = "", play: bool = False, request: Request = None):
    """
    รองรับ 2 รูปแบบ:
    1. เรียกผ่าน fetch: คืนค่า JSON { success: true, url: '...' }
    2. เรียกจากแท็ก <video> (play=True): ส่งท่อสตรีมวิดีโอ MP4 ให้เล่นสดทันที
    """
    if not id.strip():
        return {"success": False, "error": "Missing video ID"}

    # ตรวจสอบว่าเป็นการขอไฟล์วิดีโอตรงหรือไม่ (มี play=true หรือแท็ก video ร้องขอ Range)
    is_video_request = play or (request and ("video" in request.headers.get("accept", "") or "range" in request.headers))

    if is_video_request:
        return stream_video_content(id)

    # ส่ง URL สตรีมกลับไปให้ frontend
    base_url = str(request.base_url).rstrip("/") if request else "https://render.oke.dpdns.org"
    stream_url = f"{base_url}/api/stream?id={id}&play=true"
    
    return {
        "success": True,
        "url": stream_url
    }

def stream_video_content(video_id: str):
    """ดึง URL ตรงจาก yt-dlp แล้วทำตัวเป็น Proxy ส่งท่อสตรีมไปให้แท็บเล็ต/ทีวี"""
    ydl_opts = {
        # เลือกไฟล์ MP4 ที่มีทั้งภาพและเสียงรวมกัน (format 18 คือ 360p หรือ best mp4)
        "format": "18/22/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": False,
    }

    # ตรวจจับ cookies.txt อัตโนมัติ (หากมี) เพื่อกันโดน YouTube บล็อก Bot
    cookie_path = "cookies.txt" if os.path.exists("cookies.txt") else ("backend/cookies.txt" if os.path.exists("backend/cookies.txt") else None)
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

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

            # ใช้ headers ชุดเดียวกับที่ yt-dlp เจรจากับ YouTube เพื่อป้องกัน Error 403 Forbidden
            headers = info.get("http_headers", {})
            if "User-Agent" not in headers:
                headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            def iterfile():
                req = urllib.request.Request(video_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    while True:
                        chunk = response.read(64 * 1024)  # อ่านทีละ 64KB
                        if not chunk:
                            break
                        yield chunk

            return StreamingResponse(
                iterfile(),
                media_type="video/mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Type": "video/mp4",
                    "Cache-Control": "no-cache",
                }
            )

    except Exception as e:
        print(f"[STREAM ERROR] video_id={video_id} error={e}")
        raise HTTPException(status_code=500, detail=str(e))
