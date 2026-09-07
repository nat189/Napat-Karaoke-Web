import yt_dlp

def search_youtube_karaoke(query: str, max_results: int = 20):
    # 1. ใช้ Search Operator ตัด MV และระบุคาราโอเกะแบบดนตรี
    # ดึงมาเผื่อ 35 คลิปเพื่อนำมากรองทิ้งให้เหลือ 20 คลิปคุณภาพ
    search_query = f"ytsearch{max_results + 15}:{query} karaoke คาราโอเกะ -MV -\"Official MV\""
    
    ydl_opts = {
        'extract_flat': True,       # ดึงเฉพาะ metadata เพื่อความเร็วสูง
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    # คำต้องห้าม (ถ้าเจอในชื่อคลิป = ตัดทิ้งทันที ไม่เอา MV)
    EXCLUDE_KEYWORDS = [
        "OFFICIAL MV", "OFFICIAL MUSIC VIDEO", "MUSIC VIDEO", 
        "[MV]", "(MV)", " MV ", "MV/", "/MV", "TEASER"
    ]
    
    # คำที่บ่งบอกว่าเป็นคาราโอเกะเสียงดนตรีจริง (ให้คะแนนพิเศษดันขึ้นบน)
    PREFER_KEYWORDS = [
        "INSTRUMENTAL", "BACKING TRACK", "ดนตรีเปล่า", 
        "ไม่มีเสียงร้อง", "ตัดเสียงร้อง", "KARAOKE VERSION"
    ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        results = []
        
        for entry in info.get('entries', []):
            if not entry:
                continue
            
            title = entry.get("title", "ไม่ทราบชื่อเพลง")
            title_upper = f" {title.upper()} "  # เติมช่องว่างเพื่อเช็กคำเดี่ยวๆ
            
            # 2. ดักกรอง MV ออก
            is_mv = any(kw in title_upper for kw in EXCLUDE_KEYWORDS)
            if is_mv:
                continue  # ข้ามคลิปนี้ ไม่เอาเข้าผลลัพธ์
            
            thumb = ""
            if entry.get("thumbnails"):
                thumb = entry["thumbnails"][-1].get("url", "")
                
            # 3. ให้คะแนนคุณภาพคลิป (ดันคลิปดนตรีแท้ + 1080p ขึ้นบน)
            score = 0
            if any(tag in title_upper for tag in ["1080P", "1080", "FHD", "4K", "HD"]):
                score += 2
            if any(pref in title_upper for pref in PREFER_KEYWORDS):
                score += 3
            if "คาราโอเกะ" in title or "KARAOKE" in title_upper:
                score += 1
                
            results.append({
                "id": entry.get("id"),
                "videoId": entry.get("id"),
                "title": title,
                "thumbnail": thumb,
                "channel": entry.get("uploader") or entry.get("channel") or "YouTube",
                "duration": entry.get("duration_string") or "",
                "score": score
            })
        
        # จัดเรียงเอาคลิปที่คะแนนความแม่นยำสูงสุดขึ้นก่อน
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # ตัดส่งกลับตามจำนวนที่ต้องการ (20 เพลง)
        return results[:max_results]
