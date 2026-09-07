import yt_dlp

def search_youtube_karaoke(query: str, max_results: int = 20):
    # ค้นหาโดยกรองคำว่า MV ออก และดึงมาเผื่อ 45 รายการเพื่อนำมาจัดเกรดคุณภาพ
    search_query = f"ytsearch{max_results + 25}:{query} คาราโอเกะ -MV -\"Official MV\""
    
    ydl_opts = {
        'extract_flat': True,       # ดึงเฉพาะ Metadata รวดเร็วระดับมิลลิวินาที
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    # 1. แบล็กลิสต์: คำต้องห้าม (ถ้ามีคำเหล่านี้ ตัดทิ้งทันที)
    EXCLUDE_KEYWORDS = [
        "OFFICIAL MV", "OFFICIAL MUSIC VIDEO", "MUSIC VIDEO", 
        "[MV]", "(MV)", " MV ", "MV/", "/MV", "TEASER", 
        "REACTION", "BEHIND THE SCENE", "LIVE CONCERT", "DANCE PRACTICE"
    ]
    
    # 2. รายชื่อช่อง / ค่ายเพลงหลัก (Official Channels)
    GMM_CHANNELS = [
        "GMM", "GRAMMY", "GENIE", "WHITE MUSIC", "GRAND MUSIK", 
        "ONE MUSIC", "ME RECORDS", "UP G", "WERK GANG"
    ]
    RS_CHANNELS = [
        "RS", "RSFRIENDS", "RSIAM", "อาร์สยาม", "อาร์เอส"
    ]

    # 3. คำบ่งบอกว่าเป็นเสียงดนตรีต้นฉบับ / คุณภาพสูง
    MASTER_KEYWORDS = [
        "ดนตรีแท้", "ดนตรีต้นฉบับ", "OFFICIAL KARAOKE", "KARAOKE VERSION",
        "INSTRUMENTAL", "BACKING TRACK", "ตัดเสียงร้อง", "ไม่มีเสียงร้อง"
    ]

    # 4. คำบ่งบอกว่าเป็นไฟล์ MIDI / เสียงสังเคราะห์ (ลดคะแนนลง)
    MIDI_KEYWORDS = [
        "MIDI", "MID", "SOUNDFONT", "NICK", "อิเล็กโทน", "คีย์บอร์ด"
    ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        results = []
        
        for entry in info.get('entries', []):
            if not entry:
                continue
            
            title = entry.get("title", "ไม่ทราบชื่อเพลง")
            title_upper = f" {title.upper()} "
            
            channel = entry.get("uploader") or entry.get("channel") or ""
            channel_upper = channel.upper()
            
            # --- ดักกรอง MV ออก ---
            if any(kw in title_upper for kw in EXCLUDE_KEYWORDS):
                continue
            
            score = 0
            
            # --- ให้คะแนนค่าย GMM Grammy ---
            if any(gmm in channel_upper for gmm in GMM_CHANNELS):
                score += 10
            elif any(gmm in title_upper for gmm in ["GMM", "GRAMMY", "แกรมมี่"]):
                score += 8
                
            # --- ให้คะแนนค่าย RS / อาร์สยาม ---
            if any(rs in channel_upper for rs in RS_CHANNELS):
                score += 10
            elif any(rs in title_upper for rs in ["RS", "RSIAM", "RS KARAOKE", "อาร์เอส", "อาร์สยาม"]):
                score += 8

            # --- ให้คะแนนมาสเตอร์ดนตรีแท้ ---
            if any(pref in title_upper for pref in MASTER_KEYWORDS):
                score += 6
                
            # --- ให้คะแนนความละเอียดคมชัด 1080p / HD ---
            if any(hd in title_upper for hd in ["1080P", "1080", "FHD", "4K", "HD"]):
                score += 3

            # --- ให้คะแนนคำว่า คาราโอเกะ ทั่วไป ---
            if "คาราโอเกะ" in title or "KARAOKE" in title_upper:
                score += 2

            # --- หักคะแนนกรณีเป็น MIDI / ซาวด์ฟอนต์สังเคราะห์ ---
            if any(midi in title_upper for midi in MIDI_KEYWORDS):
                score -= 6
            
            thumb = ""
            if entry.get("thumbnails"):
                thumb = entry["thumbnails"][-1].get("url", "")
                
            results.append({
                "id": entry.get("id"),
                "videoId": entry.get("id"),
                "title": title,
                "thumbnail": thumb,
                "channel": channel if channel else "YouTube",
                "duration": entry.get("duration_string") or "",
                "score": score
            })
        
        # จัดเรียงลำดับ: คลิปที่ได้คะแนนสูงสุด (GMM/RS ดนตรีแท้ 1080p) จะขึ้นอยู่อันดับ 1-20
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:max_results]
