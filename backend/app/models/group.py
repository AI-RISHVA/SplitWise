  
from app.db.data import Base
from sqlalchemy import Column,Integer,String,JSON

class Group(Base):
    __tablename__="Group"
    id = Column(Integer,primary_key=True,index=True)
    group_name = Column(String,index=True)
    group_description=Column(String)
    groupmember= Column(JSON)