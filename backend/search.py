import yt_dlp

def search_youtube_karaoke(query: str, max_results: int = 6):
    search_query = f"ytsearch{max_results}:{query} คาราโอเกะ"
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        results = []
        for entry in info.get('entries', []):
            if not entry:
                continue
            thumb = ""
            if entry.get("thumbnails"):
                thumb = entry["thumbnails"][-1].get("url", "")
            results.append({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "thumbnail": thumb
            })
        return results
