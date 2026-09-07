from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from backend.search import search_youtube_karaoke

app = FastAPI(title="Napat Karaoke Pro")

# State คิวเพลง
queue: List[dict] = []
current_song: dict = None
connected_websockets: List[WebSocket] = []

class SongItem(BaseModel):
    id: str
    title: str
    thumbnail: str

async def broadcast_state():
    data = {"current": current_song, "queue": queue}
    for ws in connected_websockets:
        try:
            await ws.send_json(data)
        except Exception:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    await websocket.send_json({"current": current_song, "queue": queue})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)

@app.get("/api/search")
def api_search(q: str):
    if not q:
        return []
    return search_youtube_karaoke(q)

@app.post("/api/queue")
async def add_to_queue(song: SongItem):
    global current_song
    if current_song is None:
        current_song = song.model_dump()
    else:
        queue.append(song.model_dump())
    await broadcast_state()
    return {"status": "ok"}

@app.post("/api/next")
async def play_next():
    global current_song
    if len(queue) > 0:
        current_song = queue.pop(0)
    else:
        current_song = None
    await broadcast_state()
    return {"status": "ok"}

@app.get("/")
def get_display():
    return FileResponse("frontend/display.html")

@app.get("/remote")
def get_remote():
    return FileResponse("frontend/remote.html")
