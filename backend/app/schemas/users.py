from pydantic import BaseModel ,EmailStr ,Field 
from typing import Literal
import re

class UserIn(BaseModel):
    
    firstname : str 
    lastname : str 
    username : str 
    gender: Literal['Male', 'Female', 'other'] 
    mobile_no : str = Field(min_length=10,max_length=10,pattern=r'^\d{10}$')
    email : EmailStr
    password : str = Field(pattern=re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'))

                    # a rite pn lakhi sakay -> 


class UserOut(BaseModel):
    firstname : str 
    lastname : str
    username: str
    gender: Literal['Male', 'Female', 'other'] 
    email: EmailStr
