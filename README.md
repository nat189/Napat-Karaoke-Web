README.md (คำแนะนำในการติดตั้ง):
ควรรวมขั้นตอนติดตั้ง FFmpeg ไว้ในเอกสาร เนื่องจากเป็น Dependency ภายนอกที่จำเป็นทั้งสำหรับ yt-dlp และไลบรารีตัดต่อเสียง:

Ubuntu/Debian: sudo apt install ffmpeg

macOS: brew install ffmpeg

Windows: แนะนำให้ใส่ลิงก์หรือใช้ Dockerfile คุม Environment แทน


docker build -t karaoke-web .
