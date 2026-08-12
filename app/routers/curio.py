"""Visual-intelligence HTTP endpoints adapted from Curiora Research."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services.vision import (
    VisionBackendUnavailable,
    analyze_image,
    vision_status,
)


curio_router = APIRouter(prefix="/api/visual-intelligence", tags=["visual-intelligence"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_IMAGE_SIZE = 15 * 1024 * 1024
MAX_MESSAGE_LENGTH = 4_000


@curio_router.get("/status")
async def curio_status() -> dict[str, str | bool]:
    """Expose non-invasive model setup status for the composer UI."""

    return vision_status()


@curio_router.post("/analyze")
async def analyze_curio_image(
    image: UploadFile | None = File(default=None),
    message: str = Form(default=""),
) -> dict[str, str | bool]:
    """Validate an image, then invoke the isolated local Curio model service."""

    if image is None:
        raise HTTPException(status_code=400, detail="Add or capture an image before sending.")
    if not image.content_type or image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPEG, PNG, WEBP, or GIF image.",
        )
    if len(message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=422, detail="Keep your question under 4,000 characters.")

    image_bytes = await image.read(MAX_IMAGE_SIZE + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Images must be 15 MB or smaller.")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=ALLOWED_IMAGE_TYPES[image.content_type],
            delete=False,
        ) as temporary_file:
            temporary_file.write(image_bytes)
            temporary_path = Path(temporary_file.name)

        answer = await run_in_threadpool(analyze_image, temporary_path, message)
        return {
            "success": True,
            "answer": answer,
            "model": str(vision_status()["model"]),
            "request_id": str(uuid.uuid4()),
        }
    except VisionBackendUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        # Deliberately do not expose model/runtime stack traces to the browser.
        print("Curio image analysis failed:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Curio could not analyze that image. Please try again.",
        ) from error
    finally:
        if temporary_path is not None:
            try:
                os.remove(temporary_path)
            except OSError:
                pass
