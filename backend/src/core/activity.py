"""Activity logging — writes to MongoDB activity_logs collection."""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def log_activity(
    user_id: int,
    action: str,
    details: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
):
    """Log a user activity to MongoDB. Non-blocking — errors are logged, not raised."""
    try:
        from src.database.mongodb import get_mongodb
        db = await get_mongodb()
        await db.activity_logs.insert_one({
            "user_id": user_id,
            "action": action,
            "details": details,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Failed to log activity: {e}")
