import mimetypes
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from config import image_dir
from sale_app.config.log import Logger

logger = Logger("fly_base")
router = APIRouter()


@router.get("/file/image-preview/{file_name}")
async def image_preview(file_name: str):
    image_file_path = os.path.join(image_dir(), file_name)
    if not os.path.exists(image_file_path):
        logger.info(f"Image file not found: {image_file_path}")
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_file_path)
    with open(image_file_path, "rb") as image_file:
        return Response(content=image_file.read(), media_type=mime_type or "application/octet-stream")
