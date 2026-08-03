from pydantic import BaseModel 
from typing import Optional,List


class GroupInfo(BaseModel):
    group_name : str
    group_description:str|None = None
    groupmember: list[str]
    #Field and JSON atle import kariya km k groupmember ma set che , and db ma set and list direct convert thy nahi atle a groupmember ne json ma covert kari

    

class UpdateGroup(BaseModel):
    group_name: str  
    new_group_name: Optional[str] = None  
    group_description: Optional[str] = None  
    groupmember: Optional[List[str]] = None  
    
    old_member: Optional[str] = None  
    new_member: Optional[str] = None  