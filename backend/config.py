import os
from dotenv import load_dotenv
load_dotenv()

# --- Server ---
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# --- Image Processing ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_SIZE = (512, 512)
IMAGE_QUALITY = 95

# --- Styles ---
# NOTE: The ML pipeline used to accept a fixed style keyword (e.g. "scandinavian")
# and expanded it into a full prompt internally. It now expects a full,
# free-form design prompt directly. AVAILABLE_STYLES is kept only as a set of
# quick-pick suggestions for the client UI - it is NOT validated against
# anymore, any non-empty prompt within MIN/MAX_PROMPT_LENGTH is accepted.
AVAILABLE_STYLES = ["scandinavian", "royal", "industrial", "bohemian"]
DEFAULT_STYLE = "A tastefully redesigned room with cohesive modern furniture, natural light, and clean lines"
MIN_PROMPT_LENGTH = 3
MAX_PROMPT_LENGTH = 500

# --- ML Pipeline ---
ML_INFERENCE_STEPS = 20
ML_GUIDANCE_SCALE = 7.5
ML_TIMEOUT_SECONDS = 120

# --- Storage ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "")

# --- Cache ---
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

# --- ngrok (Kaggle) ---
NGROK_URL = "https://wackiness-spoils-manhunt.ngrok-free.dev"
USE_LOCAL_MODEL = False