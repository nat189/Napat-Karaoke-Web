import os
import subprocess

PROCESSED_DIR = "storage/processed"

def extract_instrumental(audio_path: str, video_id: str) -> str:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    output_target = f"{PROCESSED_DIR}/htdemucs/{video_id}/no_vocals.wav"
    
    # ถ้ามีไฟล์แคชอยู่แล้ว ไม่ต้องแปลงซ้ำ
    if os.path.exists(output_target):
        return output_target

    cmd = [
        "demucs",
        "--two-stems=vocals",
        audio_path,
        "-o", PROCESSED_DIR
    ]
    
    subprocess.run(cmd, check=True)
    return output_target
