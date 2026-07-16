from sqlmodel import SQLModel , Field ,JSON 
class Group(SQLModel,table = True):
    id : int |None = Field(default=None,primary_key=True)
    group_name : str = Field(index=True)
    group_description:str|None = Field(default=None)
    groupmember: list[int] = Field(default=[], sa_type=JSON)