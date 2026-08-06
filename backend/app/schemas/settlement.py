from pydantic import BaseModel

class SettlementCreate(BaseModel):
    group_name: str
    paid_to: str
    amount: float