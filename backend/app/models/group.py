

from app.db.data import Base
from sqlalchemy import Column,Integer,String,JSON

class Group(Base):
    __tablename__="Group"
    id = Column(Integer,primary_key=True,index=True)
    group_name = Column(String,index=True)
    group_description=Column(String)
    groupmember= Column(JSON)

# from typing import List , Dict
# from datetime import datetime



# from app.db.data import Base
# from sqlalchemy import Column,Integer,String,JSON


# class Expense(Base):
#     __tablename__ ="Expense"
#     id  = Column(Integer,primary_key=True,index=True)
#     group_id = Column(Integer,default=None,index=True,foreign_key="group.id")
#     group_name = Column(String,index=True)
#     paid_by_id  = Column(Integer,default=None,index=True,foreign_key="user.id")
#     paid_by_name = Column(String,default=None,index=True)
#     split_method = Column(String)
#     shared_by = Column(JSON, default=list)
#     split_details= Column(JSON, nullable=True, default=None)
#     description =Column(String,default=None)
#     # date= Column(datetime, default=datetime.now)
