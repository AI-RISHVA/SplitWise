from sqlmodel import SQLModel , Field, Column, JSON 
from typing import List , Dict
from datetime import datetime

class Expense(SQLModel,table = True):
    id : int |None = Field(default=None,primary_key=True)
    group_id : int |None = Field(default=None , foreign_key="group.id")
    group_name : str = Field(index=True)    
    paid_by_id: int | None = Field(default=None, foreign_key="user.id")
    amount : float
    paid_by_name: str = Field(default=None, index=True)
    split_method : str 
    shared_by:List[str] = Field(default=[], sa_column=Column(JSON))
    split_details: Dict[str, float] | None = Field(default=None, sa_column=Column(JSON))
    description : str |None = Field(default=None)
    date: datetime = Field(default_factory=datetime.now)


       
