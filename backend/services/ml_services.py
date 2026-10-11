import requests
from config import NGROK_URL, USE_LOCAL_MODEL
from utils.logger import get_logger

logger = get_logger("ml_services")

# Prompts for predefined styles.
STYLE_PROMPTS = {
    "scandinavian": (
        "Scandinavian interior design, minimalist furniture, "
        "light natural wood, neutral colours, soft textiles, "
        "natural lighting, clean lines, and a cozy atmosphere"
    ),
    "royal": (
        "Royal luxury interior design, elegant furniture, "
        "rich colours, sophisticated fabrics, ornate details, "
        "refined finishes, and a luxurious atmosphere"
    ),
    "industrial": (
        "Industrial interior design, exposed materials, metal "
        "accents, concrete textures, dark neutral colours, "
        "functional furniture, and an urban loft aesthetic"
    ),
}

SUPPORTED_STYLES = {*STYLE_PROMPTS, "custom"}
SUPPORTED_OPERATIONS = {"redesign", "add_furniture"}


def log_gpu_memory(stage: str):
    try:
        import torch

        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 ** 2)
            reserved = torch.cuda.memory_reserved() / (1024 ** 2)

            logger.info(
                f"[GPU] {stage} | Allocated: {allocated:.2f} MB "
                f"| Reserved: {reserved:.2f} MB"
            )
    except Exception:
        # GPU monitoring must never interrupt generation.
        pass


def load_pipeline():
    if USE_LOCAL_MODEL:
        logger.info("Local model mode - skipping pipeline load")
    else:
        logger.info(f"Using remote ngrok pipeline at {NGROK_URL}")


def generate(
    image_bytes: bytes,
    base_prompt: str = None,
    click_x: int = None,
    click_y: int = None,
    user_id: str = "default",
    *,
    style: str = None,
    custom_style_prompt: str = None,
    operation: str = "redesign",
) -> bytes:
    """
    Generate a room redesign or add furniture.

    Supported operations:
        redesign: Redesign the room in the selected style.
        add_furniture: Add furniture at the selected location.

    add_furniture requires click_x and click_y.
    """

    if USE_LOCAL_MODEL:
        raise NotImplementedError("Local model not configured")

    if not NGROK_URL:
        raise RuntimeError("ML pipeline URL is not configured")

    operation = (operation or "").strip().lower()

    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError(
            f"Unsupported operation '{operation}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_OPERATIONS))}"
        )

    if operation == "add_furniture" and (
        click_x is None or click_y is None
    ):
        raise ValueError(
            "click_x and click_y are required for add_furniture"
        )

    # Preserve compatibility with callers that omit style.
    if style is None:
        return _call_ngrok(
            image_bytes=image_bytes,
            base_prompt=base_prompt,
            click_x=click_x,
            click_y=click_y,
            user_id=user_id,
            operation=operation,
        )

    style = style.strip().lower()

    if style not in SUPPORTED_STYLES:
        raise ValueError(
            f"Unsupported style '{style}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_STYLES))}"
        )

    room_instructions = (base_prompt or "").strip()

    if not room_instructions:
        raise ValueError("Room modification instructions are required")

    if style == "custom":
        custom_style_prompt = (custom_style_prompt or "").strip()

        if not custom_style_prompt:
            raise ValueError(
                "A custom style description is required "
                "when style='custom'"
            )

        combined_prompt = (
            f"Interior design style: {custom_style_prompt}. "
            f"Room modifications: {room_instructions}. "
            "Preserve the existing room structure and maintain "
            "a photorealistic interior design."
        )

        return _call_ngrok(
            image_bytes=image_bytes,
            custom_prompt=combined_prompt,
            click_x=click_x,
            click_y=click_y,
            user_id=user_id,
            operation=operation,
        )

    return _call_ngrok(
        image_bytes=image_bytes,
        base_prompt=STYLE_PROMPTS[style],
        furniture_prompt=room_instructions,
        click_x=click_x,
        click_y=click_y,
        user_id=user_id,
        operation=operation,
    )


def _call_ngrok(
    image_bytes: bytes,
    base_prompt: str = None,
    click_x: int = None,
    click_y: int = None,
    user_id: str = "default",
    *,
    custom_prompt: str = None,
    furniture_prompt: str = None,
    operation: str = "redesign",
) -> bytes:
    try:
        files = {
            "file": ("image.jpg", image_bytes, "image/jpeg")
        }

        data = {
            "user_id": user_id,
            "operation": operation,
        }

        if base_prompt:
            data["base_prompt"] = base_prompt

        if custom_prompt:
            data["custom_prompt"] = custom_prompt

        if furniture_prompt:
            data["furniture_prompt"] = furniture_prompt

        # Forward both coordinates when provided.
        if click_x is not None:
            data["click_x"] = str(click_x)

        if click_y is not None:
            data["click_y"] = str(click_y)

        logger.info(
            f"Calling ML pipeline: {NGROK_URL}/generate "
            f"| operation={operation} "
            f"| click_x={click_x} | click_y={click_y}"
        )

        response = requests.post(
            f"{NGROK_URL.rstrip('/')}/generate",
            files=files,
            data=data,
            timeout=120,
        )

        if response.status_code != 200:
            logger.error(
                f"Pipeline error: HTTP {response.status_code}"
            )

            try:
                error_details = response.json().get("error")
            except (ValueError, AttributeError):
                error_details = None

            raise RuntimeError(
                error_details
                or f"Pipeline returned HTTP {response.status_code}"
            )

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if not content_type.startswith("image/"):
            logger.error(
                f"Unexpected pipeline response type: {content_type}"
            )
            raise RuntimeError(
                "ML pipeline returned a non-image response"
            )

        if not response.content:
            raise RuntimeError(
                "ML pipeline returned an empty image"
            )

        logger.info(
            f"Pipeline call successful | "
            f"Received {len(response.content)} bytes"
        )

        return response.content

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Pipeline timed out — Kaggle session may be busy"
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "Cannot reach pipeline — check that the ngrok URL is active"
        ) from exc


def is_pipeline_available():
    return not USE_LOCAL_MODEL and bool(NGROK_URL)