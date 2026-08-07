from datetime import datetime, timezone
from app.db.data import Base
from sqlalchemy import Column, Integer, String, Float, DateTime

class Settlement(Base):
    __tablename__ = "Settlement"
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, index=True, nullable=True)  # null thy jyre group no hoy and (1:1) settlement hoy 
    paid_by = Column(String, index=True, nullable=False)     
    paid_to = Column(String, index=True, nullable=False)     
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

