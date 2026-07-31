
from datetime import datetime,timezone

from app.db.data import Base
from sqlalchemy import Column,Integer,String,JSON,DateTime,ForeignKey,Float


class Expense(Base):
    __tablename__ ="Expense"
    id  = Column(Integer,primary_key=True,index=True)
    group_id = Column(Integer, ForeignKey("Group.id"),index=True)
    group_name = Column(String,index=True)
    paid_by_id  = Column(Integer,  ForeignKey("User.id"),index=True)
    amount =Column(Float,nullable=False, default=0.0)
    paid_by_name = Column(String,default=None,index=True)
    split_method = Column(String)
    shared_by = Column(JSON, default=list)
    split_details= Column(JSON, nullable=True, default=None)
    description =Column(String,default=None)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))