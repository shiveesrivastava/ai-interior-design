import io
from PIL import Image, UnidentifiedImageError
from config import MAX_FILE_SIZE, ALLOWED_TYPES, IMAGE_SIZE, IMAGE_QUALITY
from utils.logger import get_logger

logger = get_logger("image_utils")

# Reject images above this pixel count before resize to avoid memory spikes
MAX_IMAGE_PIXELS = 50_000_000


def validate_image(content_type: str, file_size: int) -> tuple[bool, str]:
    """
    Validate MIME type and file size.
    Called before reading file content — fast, no PIL involved.
    """
    if content_type not in ALLOWED_TYPES:
        return False, (
            f"Invalid file type: {content_type}. "
            f"Allowed: JPEG, PNG, WEBP"
        )
    if file_size == 0:
        return False, "File is empty."
    if file_size > MAX_FILE_SIZE:
        return False, "File too large. Maximum size is 10MB."
    return True, "ok"

def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Validate image content, resize to 512x512, convert to RGB JPEG.

    Raises:
        ValueError: if the file content is corrupt, not a real image,
                    or has extreme dimensions that would spike memory.
    """
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    # Step 1 — verify the file is actually a real image
    try:
        probe = Image.open(io.BytesIO(image_bytes))
        probe.verify()  # reads file data; catches renamed/corrupt files
    except UnidentifiedImageError:
        logger.warning("Corrupt or unrecognised image content")
        raise ValueError(
            "File content is not a valid image. "
            "Ensure the file is a real JPEG, PNG, or WEBP."
        )
    except Exception as e:
        logger.warning(f"Image verification failed: {e}")
        raise ValueError(f"Could not read image: {e}")

    # Step 2 — re-open after verify() since verify() closes the stream
    try:
        image = Image.open(io.BytesIO(image_bytes))

        width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            logger.warning(f"Image too large: {width}x{height}")
            raise ValueError(
                f"Image dimensions too large ({width}x{height}). "
                f"Maximum supported is ~7000x7000."
            )

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = image.resize(IMAGE_SIZE, Image.LANCZOS)

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=IMAGE_QUALITY)
        return output.getvalue()

    except ValueError:
        raise
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        raise ValueError(f"Failed to process image: {e}")