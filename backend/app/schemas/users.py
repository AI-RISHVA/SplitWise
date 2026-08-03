from pydantic import BaseModel ,EmailStr ,Field ,field_validator
from typing import Literal
import re

class UserIn(BaseModel):
    
    firstname : str 
    lastname : str 
    username : str 
    gender: Literal['Male', 'Female', 'other'] 
    mobile_no : str = Field(min_length=10,max_length=10,pattern=r'^\d{10}$')
    email : EmailStr
    password : str = Field(pattern =re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'))

    
    @field_validator('email')
    @classmethod
    def email_validator(cls,value):
        valid_domain=['gmail.com','outlook.com','yahoo.com']
        
        domain_name=value.split('@')[-1]
        if domain_name not in valid_domain:
            raise ValueError('not a valid email domain')
        return value


    @field_validator('firstname')
    @classmethod
    def firstname_validator(cls,value):
        if len(value) <3:
            raise ValueError('First name must be at least 3 characters')
        return value


    @field_validator('username')
    @classmethod
    def username_validator(cls,value):
        if len(value) <5:
            raise ValueError('First name must be at least 5 characters')
        for i in value:
            if not(i.isupper()or i.isdigit()):
                raise ValueError('Username must contain only CAPITAL letters and numbers')
        return value


class UserOut(BaseModel):
    firstname : str 
    lastname : str
    username: str
    gender: Literal['Male', 'Female', 'other'] 
    email: EmailStr

