from pydantic import BaseModel ,EmailStr ,Field ,field_validator
from typing import Literal,Optional
import re
import enum


class GenderEnum(str, enum.Enum):
    Male = "male"
    Female = "female"
    Other= "other"

class UserIn(BaseModel):
    
    firstname : str 
    lastname : str 
    username : str 
    gender: GenderEnum 
    mobile_no : str = Field(min_length=10,max_length=10,pattern=r'^\d{10}$')
    email : EmailStr
    password : str = Field(pattern =re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'))

    
    @field_validator('email')
    @classmethod
    def email_validator(cls,value):
        valid_domain=['test.com','example.com','temp.com']
        
        domain_name=value.split('@')[-1]
        if domain_name in valid_domain:
            raise ValueError('not a valid email domain')
        return value


    @field_validator('firstname')
    @classmethod
    def firstname_validator(cls,value):
        if len(value) <3:
            raise ValueError('First name must be at least 3 characters')
        return value
    
    @field_validator('lastname')
    @classmethod
    def lastname_validator(cls,value):
        if len(value) <3:
            raise ValueError('Last name must be at least 3 characters')
        return value


    @field_validator('username')
    @classmethod
    def username_validator(cls,value):
        if len(value) <5:
            raise ValueError('Username must be at least 5 characters')
        for i in value:
            if not(i.isupper()or i.isdigit()):
                raise ValueError('Username must contain only CAPITAL letters and numbers')
        return value


class UserOut(BaseModel):
    firstname : str 
    lastname : str
    username: str
    gender: Literal['male', 'female', 'other'] 
    email: EmailStr


class ProfileUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    gender: Optional[Literal['male', 'female', 'other']] = None
    email: Optional[EmailStr] = None
    mobile_no: Optional[str] = Field(default=None, min_length=10, max_length=10, pattern=r'^\d{10}$')
    email_otp: Optional[str] = Field(default=None, min_length=6, max_length=6)
    mobile_otp: Optional[str] = Field(default=None, min_length=6, max_length=6)



class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(pattern =re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'))
    confirm_password : str
    otp: str = Field(min_length=6, max_length=6) 

class ProfileOTPRequest(BaseModel):
    purpose: Literal["update_email", "update_phone"]
    target: str          # naya email ya naya 10-digit mobile number


class PasswordOTPRequest(BaseModel):
    channel: Literal["email", "phone"]   # kaha OTP bhejna hai - registered email ya phone
