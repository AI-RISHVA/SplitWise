from pydantic import BaseModel 

class GroupCreat(BaseModel):
    group_name : str
    group_description:str|None = None
    groupmember: list[str]
    #Field and JSON atle import kariya km k groupmember ma set che , and db ma set and list direct convert thy nahi atle a groupmember ne json ma covert kari
