from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class ExpenseCreate(BaseModel):
    group_name: str
    amount: float
    paid_by: str
    date: datetime| None = None 
    split_method: Literal['equally', 'unequally', 'percentage'] 
    description: str
    shared_by: list[str]
    

class SharedExpense(ExpenseCreate):
    split_details: dict[str, float] | None = None

