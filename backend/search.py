import re
import time
import threading
import yt_dlp


# ============================================================
# SEARCH CACHE
# ============================================================

CACHE_TTL = 300  # 5 นาที
SEARCH_CACHE = {}
CACHE_LOCK = threading.Lock()


def get_cached_result(cache_key):
    """ดึงผลค้นหาจาก RAM cache ถ้ายังไม่หมดอายุ"""
    now = time.time()

    with CACHE_LOCK:
        cached = SEARCH_CACHE.get(cache_key)

        if not cached:
            return None

        timestamp, results = cached

        if now - timestamp > CACHE_TTL:
            del SEARCH_CACHE[cache_key]
            return None

        # คืน copy เพื่อป้องกันข้อมูลใน cache ถูกแก้ไข
        return [dict(item) for item in results]


def set_cached_result(cache_key, results):
    """เก็บผลค้นหาไว้ใน RAM cache"""
    with CACHE_LOCK:
        SEARCH_CACHE[cache_key] = (
            time.time(),
            [dict(item) for item in results]
        )


# ============================================================
# TITLE RELEVANCE
# ============================================================

def calculate_title_relevance(title: str, query: str) -> int:
    """คำนวณความตรงกันของชื่อเพลงกับคำค้นหา"""

    q = query.strip().lower()
    t = title.lower()

    # ลบแท็กในวงเล็บ / [] เพื่อดึงชื่อเพลงเพียวๆ
    clean_t = re.sub(r'\[.*?\]|\(.*?\)', '', t)

    # ลบคำว่า karaoke
    clean_t = (
        clean_t
        .replace("คาราโอเกะ", "")
        .replace("karaoke", "")
        .strip()
    )

    # แยกส่วนด้วยเครื่องหมายขีด
    # เช่น "ขอบฟ้า - BODYSLAM"
    parts = [
        p.strip()
        for p in clean_t.split("-")
        if p.strip()
    ]

    # ========================================================
    # 1. ชื่อเพลงตรงกับคำค้นหา
    # ========================================================

    for p in parts:

        if p == q:
            return 50

        if p.startswith(q + " ") or p.endswith(" " + q):
            return 35

    # ========================================================
    # 2. คำค้นหาปรากฏเป็นคำเดี่ยว
    # ========================================================

    pattern = (
        rf'(?:^|[\s\-\(\[\{{"\'|/])'
        + re.escape(q)
        + rf'(?:$|[\s\-\)\]\}}"\'|/])'
    )

    if re.search(pattern, t):
        return 30

    # ========================================================
    # 3. ปรากฏเป็นส่วนหนึ่งของคำอื่น
    # ========================================================

    if q in t:
        return 10

    return 0


# ============================================================
# YOUTUBE KARAOKE SEARCH
# ============================================================

def search_youtube_karaoke(query: str, max_results: int = 20):

    # --------------------------------------------------------
    # Normalize query
    # --------------------------------------------------------

    query = query.strip()

    if not query:
        return []

    # จำกัด max_results ให้อยู่ในช่วงที่เหมาะสม
    max_results = max(1, min(max_results, 20))

    # --------------------------------------------------------
    # Cache key
    # --------------------------------------------------------

    cache_key = f"{query.lower()}|{max_results}"

    cached_results = get_cached_result(cache_key)

    if cached_results is not None:
        print(
            f"[SEARCH CACHE] "
            f"query='{query}' "
            f"results={len(cached_results)}"
        )

        return cached_results

    # --------------------------------------------------------
    # Search จำนวน 25 รายการ
    #
    # เดิม:
    # ytsearch{max_results + 25}
    #
    # ถ้า max_results = 20
    # เดิมจะค้น 45 รายการ
    #
    # Turbo:
    # ค้น 25 รายการ แล้วคัดเหลือ 20
    # --------------------------------------------------------

    search_count = max(25, max_results)

    search_query = (
        f"ytsearch{search_count}:"
        f"{query} คาราโอเกะ"
    )

    # --------------------------------------------------------
    # yt-dlp options
    # --------------------------------------------------------

    ydl_opts = {
        # สำคัญมาก:
        # ไม่ดึงข้อมูล format/video เต็ม
        "extract_flat": True,

        # ไม่ดาวน์โหลด
        "skip_download": True,

        # ลด output
        "quiet": True,
        "no_warnings": True,

        # ไม่ต้องโหลด playlist data เกินความจำเป็น
        "ignoreerrors": True,
    }

    # ========================================================
    # FILTER KEYWORDS
    # ========================================================

    # คำที่ใช้ตัด MV
    MV_KEYWORDS = [
        "OFFICIAL MV",
        "OFFICIAL MUSIC VIDEO",
        "MUSIC VIDEO",
        "[MV]",
        "(MV)",
        " TEASER ",
        "REACTION",
    ]

    # ช่อง GMM / RS
    GMM_RS_CHANNELS = [
        "GMM",
        "GRAMMY",
        "GENIE",
        "GENIEROCK",
        "WHITE MUSIC",
        "GRAND MUSIK",
        "UP G",
        "RS",
        "RSFRIENDS",
        "RSIAM",
        "อาร์สยาม",
    ]

    # Karaoke / Master
    MASTER_KEYWORDS = [
        "ดนตรีแท้",
        "ดนตรีต้นฉบับ",
        "OFFICIAL KARAOKE",
        "KARAOKE VERSION",
        "ORIGINAL KARAOKE",
        "INSTRUMENTAL",
        "BACKING TRACK",
    ]

    # MIDI
    MIDI_KEYWORDS = [
        "MIDI",
        "MID",
        "SOUNDFONT",
        "อิเล็กโทน",
        "คีย์บอร์ด",
    ]

    # ========================================================
    # RUN YT-DLP
    # ========================================================

    start_time = time.perf_counter()

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                search_query,
                download=False
            )

    except Exception as e:

        elapsed = time.perf_counter() - start_time

        print(
            f"[SEARCH ERROR] "
            f"query='{query}' "
            f"time={elapsed:.2f}s "
            f"error={e}"
        )

        return []

    yt_time = time.perf_counter() - start_time

    # ========================================================
    # PROCESS RESULTS
    # ========================================================

    results = []

    entries = info.get("entries", []) if info else []

    for index, entry in enumerate(entries):

        if not entry:
            continue

        # ----------------------------------------------------
        # Basic data
        # ----------------------------------------------------

        title = entry.get(
            "title",
            "ไม่ทราบชื่อเพลง"
        )

        title_upper = f" {title.upper()} "

        channel = (
            entry.get("uploader")
            or entry.get("channel")
            or ""
        )

        channel_upper = channel.upper()

        # ----------------------------------------------------
        # Filter MV
        # ----------------------------------------------------

        is_karaoke = (
            "KARAOKE" in title_upper
            or "คาราโอเกะ" in title
        )

        is_pure_mv = (
            any(
                kw in title_upper
                for kw in MV_KEYWORDS
            )
            and not is_karaoke
        )

        if is_pure_mv:
            continue

        # ====================================================
        # SCORE
        # ====================================================

        score = 0

        # ----------------------------------------------------
        # 1. ชื่อเพลงตรง
        # ----------------------------------------------------

        score += calculate_title_relevance(
            title,
            query
        )

        # ----------------------------------------------------
        # 2. อันดับจาก YouTube
        # ----------------------------------------------------

        score += max(0, 25 - index)

        # ----------------------------------------------------
        # 3. Official GMM / RS
        # ----------------------------------------------------

        if any(
            ch in channel_upper
            for ch in GMM_RS_CHANNELS
        ):
            score += 15

        elif any(
            kw in title_upper
            for kw in [
                "GMM",
                "GRAMMY",
                "GENIE",
                "RS",
                "อาร์สยาม",
            ]
        ):
            score += 10

        # ----------------------------------------------------
        # 4. Master / Karaoke
        # ----------------------------------------------------

        if any(
            pref in title_upper
            for pref in MASTER_KEYWORDS
        ):
            score += 8

        # ----------------------------------------------------
        # 5. HD / 1080p / 4K
        # ----------------------------------------------------

        if any(
            hd in title_upper
            for hd in [
                "1080P",
                "1080",
                "FHD",
                "4K",
                "HD",
            ]
        ):
            score += 4

        # ----------------------------------------------------
        # 6. หักคะแนน MIDI
        # ----------------------------------------------------

        if any(
            midi in title_upper
            for midi in MIDI_KEYWORDS
        ):
            score -= 15

        # ----------------------------------------------------
        # Thumbnail
        # ----------------------------------------------------

        thumb = ""

        if entry.get("thumbnails"):

            thumb = (
                entry["thumbnails"][-1]
                .get("url", "")
            )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        results.append({
            "id": entry.get("id"),
            "videoId": entry.get("id"),
            "title": title,
            "thumbnail": thumb,
            "channel": (
                channel
                if channel
                else "YouTube"
            ),
            "duration": (
                entry.get("duration_string")
                or ""
            ),
            "score": score,
        })

    # ========================================================
    # SORT
    # ========================================================

    sort_start = time.perf_counter()

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    results = results[:max_results]

    sort_time = time.perf_counter() - sort_start

    # ========================================================
    # SAVE CACHE
    # ========================================================

    set_cached_result(
        cache_key,
        results
    )

    total_time = time.perf_counter() - start_time

    # ========================================================
    # PERFORMANCE LOG
    # ========================================================

    print(
        f"[SEARCH] "
        f"query='{query}' "
        f"yt-dlp={yt_time:.2f}s "
        f"sort={sort_time:.4f}s "
        f"total={total_time:.2f}s "
        f"found={len(entries)} "
        f"returned={len(results)}"
    )

    return results
