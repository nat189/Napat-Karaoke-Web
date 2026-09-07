import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.services.downloader import download_youtube_audio
from backend.services.separator import extract_instrumental

app = FastAPI(title="Karaoke Web API")

# เก็บสถานะเพลงในหน่วยความจำ
tasks = {}

class TrackRequest(BaseModel):
    url: str

def process_track(video_url: str):
    try:
        tasks[video_url] = {"status": "downloading"}
        meta = download_youtube_audio(video_url)
        
        video_id = meta["video_id"]
        tasks[video_url] = {"status": "separating_vocals", "title": meta["title"]}
        
        output_file = extract_instrumental(meta["audio_path"], video_id)
        
        tasks[video_url] = {
            "status": "ready",
            "title": meta["title"],
            "stream_url": f"/media/htdemucs/{video_id}/no_vocals.wav"
        }
    except Exception as e:
        tasks[video_url] = {"status": "error", "message": str(e)}

@app.post("/api/queue")
def add_to_queue(req: TrackRequest, bg_tasks: BackgroundTasks):
    tasks[req.url] = {"status": "queued"}
    bg_tasks.add_task(process_track, req.url)
    return {"message": "Track queued", "url": req.url}

@app.get("/api/status")
def get_status(url: str):
    if url not in tasks:
        raise HTTPException(status_code=404, detail="Track not found")
    return tasks[url]

# Mount ไฟล์เสียงและหน้าเว็บ
app.mount("/media", StaticFiles(directory="storage/processed"), name="media")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
