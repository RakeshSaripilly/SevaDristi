"""
Audit Logger Service
Logs non-PII verification metadata into PostgreSQL / SQLite database.
"""

import logging
from typing import Optional
from backend.db.database import async_session
from backend.models.db_models import VerificationLog

logger = logging.getLogger("sevadristi.audit")

async def record_verification_log(
    session_id: str,
    scheme_id: str,
    overall_status: str,
    processing_mode: str
) -> Optional[str]:
    """
    Saves a redacted verification audit entry.
    Returns the log entry ID, or None if logging fails non-critically.
    """
    try:
        async with async_session() as session:
            entry = VerificationLog(
                session_id=session_id,
                scheme_id=scheme_id,
                overall_status=overall_status,
                processing_mode=processing_mode
            )
            session.add(entry)
            await session.commit()
            return entry.id
    except Exception as e:
        logger.error(f"Audit log insertion failed (non-blocking): {e}")
        return None
