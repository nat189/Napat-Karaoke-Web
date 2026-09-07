from fastapi import FastAPI
from fastapi.responses import FileResponse
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

# ==========================================
# Frontend Routes
# ==========================================

@app.get("/")
@app.get("/display")
@app.get("/display.html")
def get_display():
    return FileResponse("frontend/display.html")

@app.get("/remote")
@app.get("/controller")
@app.get("/controller.html")
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
        
        # จัดรูปแบบข้อมูลให้ตรงกับที่ controller.html เรียกใช้ (โดยเฉพาะ videoId)
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
