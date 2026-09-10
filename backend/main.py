import os
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

# ==========================================
# Frontend Routes
# ==========================================

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
# API Direct Stream (แทนที่ YouTube IFrame)
# ==========================================

@app.get("/api/stream")
def stream_video(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="Missing video id")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={id}", download=False)
            stream_url = info.get('url')
            if not stream_url:
                raise HTTPException(status_code=404, detail="Stream URL not found")
            
            # ส่ง Redirect 302 ไปยัง URL สตรีมตรง เพื่อให้เบราว์เซอร์ดึงวิดีโอมาเล่นทันที
            return RedirectResponse(url=stream_url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
