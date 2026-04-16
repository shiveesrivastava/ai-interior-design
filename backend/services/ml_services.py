import requests
from config import NGROK_URL, USE_LOCAL_MODEL
from utils.logger import get_logger

logger = get_logger("ml_services")

def load_pipeline():
    if USE_LOCAL_MODEL:
        logger.info("Local model mode - skipping pipeline load")
    else:
        logger.info(f"Using remote ngrok pipeline at {NGROK_URL}")

def generate(image_bytes: bytes, base_prompt: str = None,
             click_x: int = None, click_y: int = None,
             user_id: str = "default") -> bytes:

    if USE_LOCAL_MODEL:
        # Future: local model logic here
        raise NotImplementedError("Local model not configured")
    else:
        return _call_ngrok(image_bytes, base_prompt, 
                          click_x, click_y, user_id)

def _call_ngrok(image_bytes: bytes, base_prompt: str = None,
                click_x: int = None, click_y: int = None,
                user_id: str = "default") -> bytes:
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        
        data = {"user_id": user_id}
        if base_prompt:
            data["base_prompt"] = base_prompt
        if click_x is not None:
            data["click_x"] = str(click_x)
        if click_y is not None:
            data["click_y"] = str(click_y)

        logger.info(f"Calling ngrok pipeline: {NGROK_URL}/generate")
        
        response = requests.post(
            f"{NGROK_URL}/generate",
            files=files,
            data=data,
            timeout=120  # 2 min timeout for generation
        )

        if response.status_code == 200:
            logger.info("Pipeline call successful")
            return response.content  # returns JPEG bytes
        else:
            logger.error(f"Pipeline error: {response.status_code}")
            raise Exception(f"Pipeline returned {response.status_code}")

    except requests.exceptions.Timeout:
        raise Exception("Pipeline timed out — Kaggle session may be busy")
    except requests.exceptions.ConnectionError:
        raise Exception("Cannot reach pipeline — check ngrok URL is active")