import re
import yt_dlp

def calculate_title_relevance(title: str, query: str) -> int:
    """คำนวณความตรงกันของชื่อเพลงกับคำค้นหา"""
    q = query.strip().lower()
    t = title.lower()

    # ลบแท็กในวงเล็บและคำว่าคาราโอเกะออก เพื่อดึงชื่อเพลงเพียวๆ
    clean_t = re.sub(r'\[.*?\]|\(.*?\)|【.*?】', '', t)
    clean_t = clean_t.replace("คาราโอเกะ", "").replace("karaoke", "").strip()

    # แยกส่วนด้วยเครื่องหมายขีด (เช่น "ขอบฟ้า - BODYSLAM")
    parts = [p.strip() for p in clean_t.split("-") if p.strip()]

    # 1. ชื่อเพลงตรงกับคำค้นหาแบบเป๊ะๆ 100% (เช่น "ขอบฟ้า" vs "ขอบฟ้า")
    for p in parts:
        if p == q:
            return 50
        if p.startswith(q + " ") or p.endswith(" " + q):
            return 35

    # 2. คำค้นหาปรากฏเป็นคำเดี่ยวๆ มีขอบเขตชัดเจน (ไม่ใช่คำผสมอย่าง "ที่สุดขอบฟ้า")
    pattern = rf'(?:^|[\s\-\(\[\{{"\'|/])' + re.escape(q) + rf'(?:$|[\s\-\)\]\}}"\'|/])'
    if re.search(pattern, t):
        return 30

    # 3. ปรากฏเป็นแค่ส่วนหนึ่งของคำอื่น (เช่น "ที่สุดขอบฟ้า", "ขอบฟ้าไม่มีจริง")
    if q in t:
        return 10

    return 0

def search_youtube_karaoke(query: str, max_results: int = 20):
    # ค้นหาคำค้นหา + คาราโอเกะ (ไม่ใส่ -MV ใน query เพื่อไม่ให้กระทบ Description ของ GMM)
    search_query = f"ytsearch{max_results + 25}:{query} คาราโอเกะ"
    
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    # คำต้องห้าม (ตัดเฉพาะคลิป MV ที่ไม่ใช่คาราโอเกะ)
    MV_KEYWORDS = [
        "OFFICIAL MV", "OFFICIAL MUSIC VIDEO", "MUSIC VIDEO", 
        "[MV]", "(MV)", " TEASER ", "REACTION"
    ]
    
    GMM_RS_CHANNELS = [
        "GMM", "GRAMMY", "GENIE", "GENIEROCK", "WHITE MUSIC", 
        "GRAND MUSIK", "UP G", "RS", "RSFRIENDS", "RSIAM", "อาร์สยาม"
    ]

    MASTER_KEYWORDS = [
        "ดนตรีแท้", "ดนตรีต้นฉบับ", "OFFICIAL KARAOKE", "KARAOKE VERSION",
        "ORIGINAL KARAOKE", "INSTRUMENTAL", "BACKING TRACK"
    ]

    MIDI_KEYWORDS = ["MIDI", "MID", "SOUNDFONT", "อิเล็กโทน", "คีย์บอร์ด"]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        results = []
        entries = info.get('entries', [])
        
        for index, entry in enumerate(entries):
            if not entry:
                continue
            
            title = entry.get("title", "ไม่ทราบชื่อเพลง")
            title_upper = f" {title.upper()} "
            channel = entry.get("uploader") or entry.get("channel") or ""
            channel_upper = channel.upper()
            
            # กรอง MV ออก ยกเว้นคลิปนั้นจะระบุชัดเจนว่าเป็น Karaoke
            is_karaoke = "KARAOKE" in title_upper or "คาราโอเกะ" in title
            is_pure_mv = any(kw in title_upper for kw in MV_KEYWORDS) and not is_karaoke
            if is_pure_mv:
                continue
            
            score = 0
            
            # 1. คะแนนความตรงของชื่อเพลง (ตัวตัดสินหลัก)
            score += calculate_title_relevance(title, query)
            
            # 2. คะแนนอันดับความนิยมดั้งเดิมจาก YouTube (คลิปฮิตของ Bodyslam จะได้คะแนนสูง)
            score += max(0, 25 - index)
            
            # 3. คะแนนช่อง Official GMM (genie records / GMM Karaoke) & RS
            if any(ch in channel_upper for ch in GMM_RS_CHANNELS):
                score += 15
            elif any(kw in title_upper for kw in ["GMM", "GRAMMY", "GENIE", "RS", "อาร์สยาม"]):
                score += 10
                
            # 4. คะแนนมาสเตอร์ดนตรีแท้ / คาราโอเกะ
            if any(pref in title_upper for pref in MASTER_KEYWORDS):
                score += 8
                
            # 5. คะแนนภาพชัด 1080p
            if any(hd in title_upper for hd in ["1080P", "1080", "FHD", "4K", "HD"]):
                score += 4
                
            # หักคะแนนไฟล์เสียงสังเคราะห์ MIDI
            if any(midi in title_upper for midi in MIDI_KEYWORDS):
                score -= 15
            
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
        
        # จัดอันดับตามคะแนนความแม่นยำสูงสุด
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]
