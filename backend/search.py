import yt_dlp

def search_youtube_karaoke(query: str, max_results: int = 20):
    # เสริมคีย์เวิร์ด คาราโอเกะ HD เพื่อดึงคลิปความคมชัดสูงขึ้นมาเป็นอันดับแรก
    search_query = f"ytsearch{max_results}:{query} คาราโอเกะ HD"
    
    ydl_opts = {
        'extract_flat': True,       # ดึงเฉพาะ metadata เพื่อความรวดเร็วระดับมิลลิวินาที
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
                
            title = entry.get("title", "ไม่ทราบชื่อเพลง")
            
            # ตรวจสอบว่าในชื่อคลิปมีระบุความละเอียดสูงหรือไม่
            is_hd = any(tag in title.upper() for tag in ["1080P", "1080", "FHD", "4K", "HD"])
            
            results.append({
                "id": entry.get("id"),
                "videoId": entry.get("id"),
                "title": title,
                "thumbnail": thumb,
                "channel": entry.get("uploader") or entry.get("channel") or "YouTube",
                "duration": entry.get("duration_string") or "",
                "is_hd": is_hd
            })
        
        # จัดลำดับ: เอาคลิปที่ระบุ 1080p / HD ชัดเจนขึ้นมาก่อน
        results.sort(key=lambda x: x["is_hd"], reverse=True)
        
        return results
