from __future__ import annotations
import os
import tempfile
from pathlib import Path
from fastapi.requests import Request
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services.curio import CurioService
curio_service = CurioService()

curio_router = APIRouter(prefix="/curio",tags=["Curio routings"])

allowed_img_formats = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

max_img_size = 15 * 1024 * 1024


@curio_router.post("/analyze")
async def analyze_curio_image(request:Request,image: UploadFile = File(...),message: str = Form("")):
    """
    Analyze an uploaded image with Curio.

    Endpoint:

        POST /curio/analyze

    Form fields:

        image   -> uploaded image
        message -> user's question/instruction
    """
     #To check image content type exist
    if not image.content_type:
        raise HTTPException(status_code=400,detail="Image content type is missing.")

    #Handel the unsupported files
    if image.content_type not in allowed_img_formats:
        raise HTTPException(status_code=415,detail=("Unsupported image type. ""Please upload JPEG, PNG, WEBP, or GIF."))

    #read image and return bytes
    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400,detail="The uploaded image is empty.")

    if len(image_bytes) > max_img_size:
        raise HTTPException(status_code=413,detail="Image is too large. Maximum size is 15 MB.",)

    suffix = allowed_img_formats[image.content_type]


    temporary_path = None
    try:
        #creating temporary file for image
        with tempfile.NamedTemporaryFile(mode="wb",suffix=suffix,delete=False) as temporary_file:

            temporary_file.write(image_bytes) 
            temporary_path = Path(temporary_file.name)

        answer = await run_in_threadpool(curio_service.respond,message,str(temporary_path))

        return {"success": True,"answer": answer,}

    except FileNotFoundError:

        raise HTTPException(status_code=400,detail="the internal error occured")

    except Exception:
        raise HTTPException(status_code=500,detail=("An internall error occured Curio could not analyze the image.At this time "))

    finally:

        if temporary_path is not None:

            try:
                os.remove(temporary_path)

            except OSError:
                pass

