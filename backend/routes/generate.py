from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from utils.image_utils import validate_image, preprocess_image
from utils.logger import get_logger

logger = get_logger("generate")
router = APIRouter()

@router.get("/")
def generate_info():
    return {
        "endpoint": "/generate",
        "method": "POST",
        "input": "image file (JPEG, PNG, WEBP)",
        "output": "redesigned room image (JPEG)",
    }

@router.post("/")
async def generate_design(file: UploadFile = File(...)):
    logger.info(f"Request Recieved | Filename: {file.filename} | type: {file.content_type}")
    
    image_bytes = await file.read()

    #Validate file type and size
    is_valid, message = validate_image(file.content_type, len(image_bytes))
    if not is_valid:
        logger.warning(f"Validation Failed | {message}")
        raise HTTPException(status_code=400, detail=message)
    
    logger.info(f"Validation Passed | size: {len(image_bytes)} bytes")
    
    #Preprocess (resize to 512x512 and convert to RGB)
    preprocessed_bytes = preprocess_image(image_bytes)
    logger.info(f"Image Preprocessed | Output Size: {len(preprocessed_bytes)} bytes")

    return Response (
        content=preprocessed_bytes,
        media_type="image/jpeg"
    )