from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import uuid

app = FastAPI()

# Mount static folder to serve frontend files like index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root "/"
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# POST endpoint to download video from YouTube URL
@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")

    # Generate unique filename for download folder
    download_id = str(uuid.uuid4())
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, f"{download_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")

    # Return info to client with file id and extension
    return JSONResponse({
        "download_id": download_id,
        "filename": os.path.basename(filename),
    })

# GET endpoint to serve the downloaded file by download_id
@app.get("/download/{download_id}")
async def serve_video(download_id: str):
    download_dir = "downloads"
    # Find the file starting with download_id
    for fname in os.listdir(download_dir):
        if fname.startswith(download_id):
            file_path = os.path.join(download_dir, fname)
            if os.path.exists(file_path):
                return FileResponse(file_path, media_type="video/mp4", filename=fname)
    raise HTTPException(status_code=404, detail="File not found")
