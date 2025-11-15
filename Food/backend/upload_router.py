import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

upload_router = APIRouter()

UPLOAD_DIR = "Food/backend/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure folder exists


@upload_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # Validate type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG/PNG allowed.")

    # Generate unique filename
    ext = file.filename.split(".")[-1]
    filename = f"{datetime.utcnow().timestamp()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    file_url = f"/static/uploads/{filename}"

    return {"image_url": file_url}
