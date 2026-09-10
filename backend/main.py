import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

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
