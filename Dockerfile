FROM python:3.10-slim

# ติดตั้ง FFmpeg และ Git สำหรับดึงโมเดล
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# คัดลอกไฟล์ Dependency และติดตั้ง
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดโปรเจกต์
COPY . .

# รัน Backend Server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
