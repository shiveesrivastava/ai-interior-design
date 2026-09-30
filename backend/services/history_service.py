from supabase import create_client
from datetime import datetime, timezone

from config import (
    SUPABASE_URL,
    SUPABASE_KEY
)
from utils.logger import get_logger

logger = get_logger("history_service")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

TABLE_NAME = "generations"


async def save_generation(record: dict) -> bool:
    """
    Persist one generation (fresh or cache-hit) so it shows up in the
    user's history and can be looked up again later.

    `record` is expected to contain:
        request_id, user_id, base_prompt, click_x, click_y,
        input_url, output_url, cache_hit, processing_time_ms
    """
    try:
        payload = {
            **record,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        supabase.table(TABLE_NAME).insert(payload).execute()
        return True

    except Exception as e:
        logger.warning(f"Failed to save generation history: {e}")
        return False


async def get_user_history(user_id: str, limit: int = 20) -> list[dict]:
    """
    Return a user's past generations, most recent first.
    Returns an empty list (rather than raising) if Supabase is unreachable
    or the table doesn't exist yet, so a missing history feature never
    breaks the rest of the app.
    """
    try:
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    except Exception as e:
        logger.warning(f"Failed to fetch generation history: {e}")
        return []