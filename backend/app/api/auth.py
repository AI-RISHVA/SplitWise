
# security imports

from jose import jwt 
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta,timezone
from passlib.context import CryptContext



# 1 congiguration
SECRET_KEY = "rishvasecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# 2.PASSWORD HAHING SETUP

pwd_context = CryptContext(schemes =["bcrypt"],deprecated ="auto")

# hash password
def hash_password(password:str):
    return pwd_context.hash(password)

# verify password
def verifypass(plain_password,hash_password):
    return pwd_context.verify(plain_password,hash_password)


# 3.creare token


def create_token(data: dict):
    to_encode = data.copy() # Original data ki duplicate copy banayi
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # 30 min baad ka time nikala
    to_encode.update({"exp": expire}) # Data ke andar 'exp' naam se expiry time jod diya
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # Data + Chabi + Formula milakar token banaya
    return token

# 4.token varification

#OAuthsetup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "login")


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") #basic identity(jaise user ka email ya username, jise standard terms mein "sub" kehte hain
        if username is None:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token"
            )
        return username
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )   
