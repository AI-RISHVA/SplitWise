from sqlmodel import SQLModel , Field
class User(SQLModel,table = True):
    id : int |None = Field(default=None,primary_key=True)
    firstname : str = Field(index=True)
    lastname : str = Field(index=True)
    username : str = Field(index=True,unique=True)
    gender : str
    mobile_no : str = Field(min_length=10,max_length=10)    
    email : str = Field(unique=True, nullable=False, index=True)
    password : str = Field( nullable=False)
