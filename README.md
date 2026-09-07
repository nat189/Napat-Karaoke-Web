README.md (คำแนะนำในการติดตั้ง):
ควรรวมขั้นตอนติดตั้ง FFmpeg ไว้ในเอกสาร เนื่องจากเป็น Dependency ภายนอกที่จำเป็นทั้งสำหรับ yt-dlp และไลบรารีตัดต่อเสียง:

Ubuntu/Debian: sudo apt install ffmpeg

macOS: brew install ffmpeg

Windows: แนะนำให้ใส่ลิงก์หรือใช้ Dockerfile คุม Environment แทน

cd /mnt/cache/appdata

git clone https://github.com/nat189/Napat-Karaoke-Web.git karaoke-web

cd karaoke-web

docker build -t karaoke-web .


cd /mnt/cache/appdata/karaoke-web

# ดึงโค้ดใหม่
git pull

# ลบคอนเทนเนอร์ตัวเก่า
docker stop karaoke-web
docker rm karaoke-web

# Build ใหม่อีกครั้ง (รอบนี้จะเสร็จไวมากเพราะไม่มีโมเดล AI)
docker build -t karaoke-web .

# สั่งรันคอนเทนเนอร์
docker run -d \
  --name karaoke-web \
  --restart unless-stopped \
  -p 8085:8000 \
  karaoke-web
