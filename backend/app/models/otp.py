from sqlalchemy import Column, String, Float, Integer
from app.db.data import Base  # Jo bhi aapka Base class import ho

class OTPStore(Base):
    __tablename__ = "otp_store"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False) # Email or Mobile
    otp = Column(String, nullable=False)
    expires_at = Column(Float, nullable=False) # Timestamp (seconds me)
    sent_at = Column(Float, nullable=False)    
