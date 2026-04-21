from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query 
from fastapi.responses import Response
from services.ml_services import generate, log_gpu_memory, is_pipeline_available
from utils.image_utils import validate_image, preprocess_image
from utils.logger import get_logger
from config import DEFAULT_STYLE
import base64
import uuid
import time
import asyncio

router = APIRouter()
logger = get_logger("generate_router")

total_requests = 0
success_requests = 0
failed_requests = 0
active_requests = 0

def log_stats():
    """Log statistics every 10 requests"""
    global total_requests, success_requests, failed_requests, active_requests
    if total_requests % 10 == 0:
        success_rate = (success_requests / total_requests) * 100 if total_requests > 0 else 0
        logger.info(
            f"[STATS] Total: {total_requests} | "
            f"Success: {success_requests} | "
            f"Failed: {failed_requests} | "
            f"Success Rate: {success_rate:.2f}%"
        )

@router.post("/generate/")
async def generate_design(
    file: UploadFile = File(...),
    base_prompt: str = Form(DEFAULT_STYLE),
    click_x: int = Form(None),
    click_y: int = Form(None),
    user_id: str = Form("default"),
    format: str = Query("raw", pattern="^(raw|base64)$")
):
    global total_requests, success_requests, failed_requests, active_requests
    active_requests += 1
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    total_requests += 1
    logger.info(f"[REQ-{request_id}] Request received | file={file.filename}")

    filename = file.filename.lower()
    if not filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .jpg, .jpeg, .png, .webp")

    # Read file
    image_bytes = await file.read()
    logger.info(f"[REQ-{request_id}] File size: {len(image_bytes)} bytes")

    # Validate
    is_valid, message = validate_image(file.content_type, len(image_bytes))
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    validate_time = time.time()
    logger.info(f"[REQ-{request_id}] Validation done in {(validate_time - start_time)*1000:.2f} ms")

    # Preprocess
    try:
        processed_bytes = preprocess_image(image_bytes)
    except Exception as e:
        logger.error(f"[REQ-{request_id}] Image preprocessing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid image content or dimensions.")
    
    preprocess_time = time.time()
    logger.info(f"[REQ-{request_id}] Preprocessing done in {(preprocess_time - validate_time)*1000:.2f} ms")

    log_gpu_memory("before generation")

    # Call ML (this goes to ngrok)
    try:
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"[REQ-{request_id}] ML attempt {attempt}")

                result_bytes = await asyncio.wait_for(
                    asyncio.to_thread(
                        generate,
                        processed_bytes,
                        base_prompt,
                        click_x,
                        click_y,
                        user_id
                    ),
                    timeout=120
                )

                break  # success → exit loop

            except Exception as e:
                logger.warning(f"[REQ-{request_id}] ML attempt {attempt} failed: {e}")

                if attempt == max_attempts:
                    raise e  # rethrow after last attempt

        ml_time = time.time()
        logger.info(f"[REQ-{request_id}] ML generation done in {(ml_time - preprocess_time)*1000:.2f} ms")

        if len(result_bytes) > 5 * 1024 * 1024:
            logger.warning(f"[REQ-{request_id}] Large response detected: {len(result_bytes)} bytes")

        total_time = time.time()
        logger.info(f"[REQ-{request_id}] Total processing time: {(total_time - start_time)*1000:.2f} ms")
        
        success_requests += 1
        log_stats()
        log_gpu_memory("after generation")

        if format == "base64":
            encoded = base64.b64encode(result_bytes).decode()
            return { "image_base64": encoded }
        
        return Response(content=result_bytes, 
                        media_type="image/jpeg",
                        headers={"Content-Disposition": 'inline; filename="redesigned_room.jpg"'})
    
    except asyncio.TimeoutError:
        failed_requests += 1
        log_stats()
        logger.error(f"[REQ-{request_id}] ML request timed out")
        raise HTTPException(
            status_code=504,
            detail="Image generation timed out."
        )

    except Exception as e:
        failed_requests += 1
        log_stats()
        
        error_msg = str(e).lower()
        logger.error(f"[REQ-{request_id}] ML Pipeline error: {e}")

        total_time = time.time()
        logger.info(f"[REQ-{request_id}] Total processing time (failed): {(total_time - start_time)*1000:.2f} ms")

        if "timeout" in error_msg:
            raise HTTPException(status_code=504, detail="Image generation timed out. Please try again.")
        elif any(keyword in error_msg for keyword in ["connection", "quota", "exhaust", "unavailable"]):
            raise HTTPException(
                status_code=503,
                detail="ML service unavailable (GPU may be exhausted). Try again later."
            )
        else:
            raise HTTPException(status_code=500, detail="Image Generation Failed.")
        
    finally:
        active_requests -= 1
               
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

@router.get("/stats")
def get_stats():
    global total_requests, success_requests, failed_requests, active_requests

    success_rate = 0.0
    if total_requests > 0:
        success_rate = (success_requests / total_requests) * 100

    return {
        "total_requests": total_requests,
        "success_requests": success_requests,
        "failed_requests": failed_requests,
        "success_rate": round(success_rate, 2),
        "warning": "Stats are per-worker in multi-worker setups and may not reflect global totals."
    }

@router.get("/health")
def health_check():
    pipeline_status = "loaded" if is_pipeline_available() else "not_loaded"

    return {
        "status": "healthy",
        "pipeline_status": pipeline_status
    }