README.md (คำแนะนำในการติดตั้ง):
ควรรวมขั้นตอนติดตั้ง FFmpeg ไว้ในเอกสาร เนื่องจากเป็น Dependency ภายนอกที่จำเป็นทั้งสำหรับ yt-dlp และไลบรารีตัดต่อเสียง:

Ubuntu/Debian: sudo apt install ffmpeg

macOS: brew install ffmpeg

Windows: แนะนำให้ใส่ลิงก์หรือใช้ Dockerfile คุม Environment แทน

cd /mnt/cache/appdata

git clone https://github.com/nat189/Napat-Karaoke-Web.git karaoke-web

cd karaoke-web

docker build -t karaoke-web .
