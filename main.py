from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess
import uuid
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve frontend files from /static
app.mount("/static", StaticFiles(directory="static"), name="static")

class VideoRequest(BaseModel):
    url: str

@app.post("/download")
async def download_video(data: VideoRequest):
    url = data.url
    video_id = str(uuid.uuid4())
    output_template = f"downloads/{video_id}.%(ext)s"

    os.makedirs("downloads", exist_ok=True)

    command = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ]

    try:
        subprocess.run(command, check=True)
        file_path = f"downloads/{video_id}.mp4"
        if os.path.exists(file_path):
            return {"status": "success", "file": f"/download/{video_id}"}
        else:
            return {"status": "error", "message": "File not found after download."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/{video_id}")
async def serve_video(video_id: str):
    file_path = f"downloads/{video_id}.mp4"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=f"{video_id}.mp4")
    else:
        return {"status": "error", "message": "Video not found."}
