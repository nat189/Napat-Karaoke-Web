FROM python:3.11-slim

# ติดตั้ง ffmpeg, git และ nodejs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# บังคับติดตั้ง PyTorch และ TorchAudio แบบ CPU Only (ตัด CUDA/NVIDIA ออกทั้งหมด)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
