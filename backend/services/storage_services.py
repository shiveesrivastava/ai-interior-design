from supabase import create_client

from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

async def upload_image(
    image_bytes: bytes,
    filename: str
) -> str | None:
    try:
        supabase.storage.from_(
            SUPABASE_BUCKET
        ).upload(
            filename,
            image_bytes,
            {
                "content-type": "image/jpeg"
            }
        )
        public_url = (
            supabase.storage
            .from_(SUPABASE_BUCKET)
            .get_public_url(filename)
        )
        return public_url

    except Exception as e:
        print(f"Upload failed: {e}")
        return None
    
async def delete_image(
    filename: str
) -> bool:
    try:
        supabase.storage.from_(
            SUPABASE_BUCKET
        ).remove([filename])
        return True

    except Exception as e:
        print(f"Delete failed: {e}")
        return False