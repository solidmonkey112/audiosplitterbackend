import os
import uuid
import subprocess
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Enable CORS so Vercel can talk to Railway
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Mount storage (Railway Volume should be at /app/data)
STORAGE_PATH = "/app/data"
os.makedirs(f"{STORAGE_PATH}/output", exist_ok=True)
app.mount("/stems", StaticFiles(directory=f"{STORAGE_PATH}/output"), name="stems")

@app.post("/process")
async def process_audio(file: UploadFile, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    input_path = f"{STORAGE_PATH}/{job_id}.mp3"
    with open(input_path, "wb") as f:
        f.write(await file.read())
    
    background_tasks.add_task(run_demucs, job_id, input_path)
    return {"job_id": job_id, "status": "processing"}

def run_demucs(job_id, input_path):
    out_dir = f"{STORAGE_PATH}/output/{job_id}"
    # Using 6-stem model for Lead/Harmony/Acoustic/Electric separation
    subprocess.run(["demucs", "-n", "htdemucs_6s", "-o", out_dir, input_path])
    os.remove(input_path) # Clean up