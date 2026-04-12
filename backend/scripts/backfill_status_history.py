"""One-time backfill script for Application.status_history.

Populates status_history for existing applications using this rule:
  - Always: 1 entry at created_at with status="pending",
    actor = the applicant, note = None.
  - If current status != "pending": 1 additional entry at updated_at
    with the current status, actor_id = None, actor_name = "System (backfill)",
    and note = submission_note or revision_note or None.

Usage (from the backend/ directory):

    python3 scripts/backfill_status_history.py
"""
import asyncio
from tortoise import Tortoise
from src.database.postgres import TORTOISE_ORM
from src.applications.models import Application
from src.users.models import User


async def backfill():
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        applications = await Application.all()
        updated = 0
        for app in applications:
            if app.status_history:
                continue  # skip rows that already have history
            applicant = await User.filter(id=app.applicant_id).first()
            actor_name = (applicant.full_name or applicant.username) if applicant else "Unknown"
            history = [{
                "status": "pending",
                "timestamp": app.created_at.isoformat(),
                "actor_id": app.applicant_id,
                "actor_name": actor_name,
                "note": None,
            }]
            if app.status.value != "pending":
                history.append({
                    "status": app.status.value,
                    "timestamp": app.updated_at.isoformat(),
                    "actor_id": None,
                    "actor_name": "System (backfill)",
                    "note": app.submission_note or app.revision_note or None,
                })
            app.status_history = history
            await app.save(update_fields=["status_history"])
            updated += 1

        print(f"Backfilled status_history for {updated} application(s)")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(backfill())
