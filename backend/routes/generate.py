from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query 
from services.ml_services import generate, log_gpu_memory, is_pipeline_available
from utils.image_utils import validate_image, preprocess_image
from utils.logger import get_logger
from services.storage_services import upload_image
from services.cache_services import generate_cache_key, get_from_cache, save_to_cache
from services.history_service import save_generation, get_user_history
from config import DEFAULT_STYLE, MIN_PROMPT_LENGTH, MAX_PROMPT_LENGTH
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
    force_regenerate: bool = Form(False),
    format: str = Query("raw", pattern="^(raw|base64)$")
):
    global total_requests, success_requests, failed_requests, active_requests
    active_requests += 1
    request_id = str(uuid.uuid4())[:8]
    input_filename = f"input_{request_id}.jpg"
    output_filename = f"output_{request_id}.jpg"
    start_time = time.time()
    total_requests += 1
    logger.info(f"[REQ-{request_id}] Request received | file={file.filename}")

    filename = file.filename.lower()
    if not filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .jpg, .jpeg, .png, .webp")

    # base_prompt is now a full custom design prompt (not a fixed style
    # keyword), so validate it by length rather than against a fixed list.
    base_prompt = base_prompt.strip() if base_prompt else DEFAULT_STYLE
    if not (MIN_PROMPT_LENGTH <= len(base_prompt) <= MAX_PROMPT_LENGTH):
        raise HTTPException(
            status_code=400,
            detail=f"base_prompt must be between {MIN_PROMPT_LENGTH} and {MAX_PROMPT_LENGTH} characters."
        )

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
        logger.error(
            f"[REQ-{request_id}] Image preprocessing error: {e}"
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid image content or dimensions."
        )

    # Generate cache key
    cache_key = generate_cache_key(
        processed_bytes,
        base_prompt,
        click_x,
        click_y
    )

    # Check Redis cache (skipped entirely when the user asks to regenerate)
    if not force_regenerate:
        try:
            cached_response = await get_from_cache(cache_key)
            if cached_response is not None:
                success_requests += 1
                log_stats()

                cache_time = time.time()
                logger.info(
                    f"[REQ-{request_id}] Cache HIT | "
                    f"Key={cache_key[:12]} | "
                    f"Latency={(cache_time-start_time)*1000:.2f} ms"
                )
                cached_response["cache_hit"] = True
                cached_response["processing_time_ms"] = round(
                    (cache_time - start_time) * 1000, 2
                )

                try:
                    await save_generation({
                        "request_id": request_id,
                        "user_id": user_id,
                        "base_prompt": base_prompt,
                        "click_x": click_x,
                        "click_y": click_y,
                        "input_url": cached_response.get("input_url"),
                        "output_url": cached_response.get("output_url"),
                        "cache_hit": True,
                        "processing_time_ms": cached_response.get("processing_time_ms"),
                    })
                except Exception as e:
                    logger.warning(f"[REQ-{request_id}] Failed to save history (cache hit): {e}")

                return cached_response

            logger.info(
                f"[REQ-{request_id}] Cache MISS | Key={cache_key[:12]}"
            )

        except Exception as e:
            logger.warning(
                f"[REQ-{request_id}] Redis unavailable: {e}"
            )
            logger.info(
                f"[REQ-{request_id}] Continuing without cache."
            )
    else:
        logger.info(f"[REQ-{request_id}] force_regenerate=True | Skipping cache lookup")
    
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
        try:
            input_url = await upload_image(
                processed_bytes,
                input_filename
            )
            logger.info(
                f"[REQ-{request_id}] Input image uploaded: {input_url}"
            )
        except Exception as e:
            logger.warning(
                f"[REQ-{request_id}] Input upload failed: {e}"
            )
            input_url = None
        try:
            output_url = await upload_image(
                result_bytes,
                output_filename
            )
        except Exception as e:
            logger.warning(
                f"[REQ-{request_id}] Output upload failed: {e}"
            )
            output_url = None
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
            try:
                await save_generation({
                    "request_id": request_id,
                    "user_id": user_id,
                    "base_prompt": base_prompt,
                    "click_x": click_x,
                    "click_y": click_y,
                    "input_url": input_url,
                    "output_url": output_url,
                    "cache_hit": False,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                })
            except Exception as e:
                logger.warning(f"[REQ-{request_id}] Failed to save history: {e}")
            return { "image_base64": encoded }
        
        response_data = {
            "status": "success",
            "request_id": request_id,
            "cache_hit": False,
            "input_url": input_url,
            "output_url": output_url,
            "processing_time_ms": round(
                (total_time - start_time) * 1000,
                2
            )
        }

        try:
            await save_to_cache(
                cache_key,
                response_data
            )

        except Exception as e:
            logger.warning(
                f"[REQ-{request_id}] Failed to save cache: {e}"
            )

        try:
            await save_generation({
                "request_id": request_id,
                "user_id": user_id,
                "base_prompt": base_prompt,
                "click_x": click_x,
                "click_y": click_y,
                "input_url": input_url,
                "output_url": output_url,
                "cache_hit": False,
                "processing_time_ms": response_data["processing_time_ms"],
            })
        except Exception as e:
            logger.warning(f"[REQ-{request_id}] Failed to save history: {e}")

        return response_data
    
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
        logger.info(
            f"[REQ-{request_id}] Failed request | "
            f"Latency={(total_time-start_time)*1000:.2f} ms"
        )

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
            "click_coordinates_supported": True,
            "custom_prompt_supported": True,
            "force_regenerate_supported": True,
            "history_supported": True
        },
        "prompt_constraints": {
            "min_length": MIN_PROMPT_LENGTH,
            "max_length": MAX_PROMPT_LENGTH
        }
    }

@router.get("/history")
async def get_history(user_id: str = Query("default"), limit: int = Query(20, ge=1, le=100)):
    """
    Return a user's past generations, most recent first, so the client can
    either display them (view history) or resubmit with force_regenerate=true
    for a fresh version.
    """
    records = await get_user_history(user_id, limit)
    return {
        "user_id": user_id,
        "count": len(records),
        "results": records
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