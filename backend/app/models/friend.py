from sqlalchemy import Column, Integer, String, Enum, DateTime
from app.db.data import Base
from datetime import datetime, timezone
import enum

class FriendStatus(str, enum.Enum): # enum - use for fixed option

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    
    sender_username = Column(String, index=True, nullable=False)
    receiver_username = Column(String, index=True, nullable=False)
    status = Column(String, default=FriendStatus.PENDING , nullable=False)  # ahiya call kariyu che function ne
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
