
from app.db.data import Base
from app.schemas.users import GenderEnum
from sqlalchemy import Column,Integer,String , Boolean
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ ="User"
    id = Column(Integer,primary_key=True, index=True)
    firstname = Column(String,index=True)
    lastname = Column(String,index=True)
    username = Column(String,index=True,unique=True)
    gender = Column(String, default=GenderEnum.Female, nullable=False) 
    mobile_no =Column(String(10))    
    email =Column(String,unique=True, nullable=False, index=True)
    password =Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
