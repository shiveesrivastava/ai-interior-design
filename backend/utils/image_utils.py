from PIL import Image
import io

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image(content_type: str, file_size: int) -> tuple[bool, str]:
    if content_type not in ALLOWED_TYPES:
        return False, f"Invalid file type: {content_type}. Allowed: JPEG, PNG, WEBP"
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is 10MB"
    return True, "ok"

def preprocess_image(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB (handles PNG with transparency)
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Resize to 512x512 (required by Stable Diffusion)
    image = image.resize((512, 512), Image.LANCZOS)
    
    # Convert back to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()