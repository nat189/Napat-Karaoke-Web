import os
import yt_dlp

RAW_DIR = "storage/raw"

def download_youtube_audio(youtube_url: str) -> dict:
    os.makedirs(RAW_DIR, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{RAW_DIR}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        video_id = info['id']
        title = info.get('title', 'Unknown')
        audio_path = f"{RAW_DIR}/{video_id}.mp3"

    return {"video_id": video_id, "title": title, "audio_path": audio_path}
