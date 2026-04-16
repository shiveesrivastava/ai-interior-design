from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from services.ml_services import generate
from utils.image_utils import validate_image, preprocess_image
from utils.logger import get_logger
from config import DEFAULT_STYLE

router = APIRouter()
logger = get_logger("generate_router")

@router.post("/generate/")
async def generate_design(
    file: UploadFile = File(...),
    base_prompt: str = Form(DEFAULT_STYLE),
    click_x: int = Form(None),
    click_y: int = Form(None),
    user_id: str = Form("default")
):
    logger.info(f"Request received | file={file.filename}")

    # Read file
    image_bytes = await file.read()

    # Validate
    is_valid, message = validate_image(file.content_type, len(image_bytes))
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    # Preprocess
    try:
        processed_bytes = preprocess_image(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Call ML (this goes to ngrok)
    try:
        result_bytes = generate(
            image_bytes=processed_bytes,
            base_prompt=base_prompt,
            click_x=click_x,
            click_y=click_y,
            user_id=user_id
        )
        return Response(content=result_bytes, media_type="image/jpeg")

    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))