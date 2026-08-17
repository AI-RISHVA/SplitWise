
# security imports

from jose import jwt 
from fastapi import Body,APIRouter , Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta,timezone
from passlib.context import CryptContext
from app.schemas.refreshtoken import RefreshTokenInput

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.data import get_session
from app.models.token_blacklist import BlacklistedToken
router = APIRouter()

# 1 congiguration
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int( os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",30))

# 2.PASSWORD HAHING SETUP

pwd_context = CryptContext(schemes =["bcrypt"])

# hash password
def hash_password(password:str):
    return pwd_context.hash(password)

# verify password
def verifypass(plain_password,hash_password):
    return pwd_context.verify(plain_password,hash_password)


# 3.creare token


def create_token(data: dict , expires_delta: timedelta = None, is_refresh: bool = False):
    to_encode = data.copy() # Original data ki duplicate copy banayi

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 10 minute for access token, 7 days for refresh token
        current_time = datetime.now(timezone.utc)
        if is_refresh:
            lifespan = timedelta(days=7)
        else:
            lifespan = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = current_time + lifespan

    to_encode.update({"exp": expire, "type": "refresh" if is_refresh else "access"})
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # Data + Chabi + Formula milakar token banaya
    return token



# 4.token varification

#OAuthsetup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):

    
    blacklisted = db.execute(select(BlacklistedToken).where(BlacklistedToken.token == token)).scalars().first()
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been logged out. Please login again.")

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





@router.post("/refresh")
def refresh_access_token(data: RefreshTokenInput,db: Session = Depends(get_session)):
    refresh_token = data.refresh_token

    blacklisted = db.execute(
        select(BlacklistedToken).where(BlacklistedToken.token == refresh_token)
    ).scalars().first()
    
    if blacklisted:
        raise HTTPException(status_code=401, detail="Refresh token has been logged out. Please login again.")

    try:
        #  Refresh token ne decode and verify 
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh" or username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Refresh token has expired or is invalid")

    # jo token sachu hoy to refresh token create kari de
    new_access_token = create_token({"sub": username}, is_refresh=False)
    
    return {
        "access_token":new_access_token,
        "token_type":"bearer"
    }
