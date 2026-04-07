import os

# --- Server ---
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# --- Image Processing ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_SIZE = (512, 512)
IMAGE_QUALITY = 95

# --- Styles ---
AVAILABLE_STYLES = ["scandinavian", "royal", "industrial", "bohemian"]
DEFAULT_STYLE = "scandinavian"

# --- ML Pipeline ---
ML_INFERENCE_STEPS = 20
ML_GUIDANCE_SCALE = 7.5

# --- Storage (Week 3) ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Cache (Week 3) ---
REDIS_URL = os.getenv("REDIS_URL", "")