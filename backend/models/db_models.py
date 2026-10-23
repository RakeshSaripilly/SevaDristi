"""
SQLAlchemy Database Models for SevaDristi
STRICT PRIVACY POLICY:
- NO PII (No names, no Aadhaar, no DOB, no phone/addresses)
- NO raw image data or binary documents
- Only non-reversible UUIDs and aggregate verification telemetry
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from backend.db.database import Base

class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    session_id = Column(
        String(36),
        nullable=False,
        index=True
    )
    scheme_id = Column(
        String(64),
        nullable=False,
        index=True
    )
    overall_status = Column(
        String(32),
        nullable=False
    )
    processing_mode = Column(
        String(16),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "scheme_id": self.scheme_id,
            "overall_status": self.overall_status,
            "processing_mode": self.processing_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
