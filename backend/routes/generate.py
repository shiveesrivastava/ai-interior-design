from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from services.ml_services import generate
from utils.image_utils import validate_image, preprocess_image
from utils.logger import get_logger
from config import DEFAULT_STYLE
import base64

router = APIRouter()
logger = get_logger("generate_router")

@router.post("/generate/")
async def generate_design(
    file: UploadFile = File(...),
    base_prompt: str = Form(DEFAULT_STYLE),
    click_x: int = Form(None),
    click_y: int = Form(None),
    user_id: str = Form("default"),
    format: str = "raw"
):
    logger.info(f"Request received | file={file.filename}")

    filename = file.filename.lower()
    if not filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .jpg, .jpeg, .png, .webp")

    # Read file
    image_bytes = await file.read()
    logger.info(f"File Size: {len(image_bytes)} bytes")

    # Validate
    is_valid, message = validate_image(file.content_type, len(image_bytes))
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    # Preprocess
    try:
        processed_bytes = preprocess_image(image_bytes)
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid image content or dimensions.")

    # Call ML (this goes to ngrok)
    try:
        result_bytes = generate(
            image_bytes=processed_bytes,
            base_prompt=base_prompt,
            click_x=click_x,
            click_y=click_y,
            user_id=user_id
        )

        if len(result_bytes) > 5 * 1024 * 1024:
            logger.warning(f"Generated image is large: {len(result_bytes)} bytes")
        if format == "base64":
            encoded = base64.b64encode(result_bytes).decode()
            return { "image_base64": encoded }
        if format not in ["raw", "base64"]:
            raise HTTPException(status_code=400, detail="Invalid format. Allowed: raw, base64")
        
        return Response(content=result_bytes, media_type="image/jpeg",
                        headers={"Content-Disposition": 'inline; filename="redesigned_room.jpg"'})

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"ML Pipeline error: {e}")
        if "timeout" in error_msg:
            raise HTTPException(status_code=504, detail="Image generation timed out. Please try again.")
        elif "connection" in error_msg:
            raise HTTPException(status_code=503, detail="Cannot reach image generation service. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail="Image Generation Failed.")
        
@router.get("/generate/metadata")
def get_metadata():
    return {
        "output_image": {
            "format": "JPEG",
            "dimensions": "512x512",
            "quality": 95
        },
        "input_constraints": {
            "max_file_size": "10MB",
            "allowed_formats": ["jpg", "jpeg", "png", "webp"]
        },
        "features": {
            "base64_supported": True,
            "click_coordinates_supported": True
        }
    }