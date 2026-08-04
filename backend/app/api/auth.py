
# security imports

from jose import jwt 
from fastapi import Body,APIRouter , Depends, HTTPException, status
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


def create_token(data: dict , expires_delta: timedelta = None, is_refresh: bool = False):
    to_encode = data.copy() # Original data ki duplicate copy banayi

    if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Agar refresh token hai toh 7 din, nahi toh access token ke liye 15 mins
        expire = datetime.now(timezone.utc) + (timedelta(days=7) if is_refresh else timedelta(minutes=15))

    to_encode.update({"exp": expire , "type": "refresh" if is_refresh else "access"}) # Data ke andar 'exp' naam se expiry time jod diya
    
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




router = APIRouter()
@router.post("/refresh")
def refresh_access_token(refresh_token: str = Body(..., embed=True)):
    try:
        #  Refresh token ko decode aur verify karein
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        #  Check karein ki bheja gaya token sach me 'refresh' token hi hai ya nahi
        if token_type != "refresh" or username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Refresh token has expired or is invalid")

    # Agar token sahi hai, toh ek NAYA Access Token generate karke de dein
    new_access_token = create_token({"sub": username}, is_refresh=False)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
