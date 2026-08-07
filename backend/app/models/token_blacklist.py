from datetime import datetime, timezone
from app.db.data import Base
from sqlalchemy import Column, Integer, String, DateTime

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))