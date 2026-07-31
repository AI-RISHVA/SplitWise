from fastapi import APIRouter ,FastAPI,Depends, HTTPException,status
from app.db.data import get_session
from app.schemas.users import UserOut,UserIn
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List

# table import
from app.models.expense import Expense  
from app.models.group import Group
from app.models.user import User


# security imports
app = FastAPI()
from jose import jwt 
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from datetime import datetime,timedelta,timezone
from passlib.context import CryptContext


# database error handling import
from sqlalchemy.exc import IntegrityError


router = APIRouter()
 ### app.inculde_router(user_routes) #a line main file ma lakhvi jethi a file na endpoints tya jova malse

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
        payload = jwt.decode(token, SECRET_KEY, algorithms={ALGORITHM})
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

# login api (token genrate with oauth2)

@app.post("/login")
def login(form_data :OAuth2PasswordRequestForm=Depends(),db: Session = Depends(get_session)
):
    user = db.execute(select(User).where(User.username == form_data.username)).scalars().first() 
    if not user or not verifypass(form_data.password,user.password):
        raise HTTPException(
            status_code=400,
            detail="invalid username & password"
        )

    access_token = create_token({"sub":form_data.username})

    return {
        "access_token " :access_token,
        "token_type":"bearer"
    }



@router.post("/register",response_model=UserOut)
async def user_register(signin:UserIn,db: Session = Depends(get_session)):
    try:
        db_user = User(
            firstname =signin.firstname,
            lastname =signin.lastname,
            username =signin.username,
            gender =signin.gender,
            mobile_no =signin.mobile_no,
            email =signin.email,
            password =hash_password(signin.password),
            
        )
        db.add(db_user) #db na session ma add kare
        
        db.commit() #db ma save kare
        
        db.refresh(db_user)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
    
        return db_user
    except IntegrityError as e:
        db.rollback() # if koi error avse to db rollback kare(atle ke "undo" kare)
        error_msg = str(e.orig)
        
        if "user.username" in error_msg or "UNIQUE constraint failed: user.username" in error_msg:
            detail_msg = "Username already exists. Please choose a unique username."
        elif "user.email" in error_msg or "UNIQUE constraint failed: user.email" in error_msg:
            detail_msg = "Email is already registered. Please use another email."
        else:
            detail_msg = "This user data already exists."

        # 3. Server crash karne ke bajay client ko 400 Error bhejien
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    


@router.get("/register_view", response_model=List[UserOut])
async def user_view(db: Session = Depends(get_session)):
    users = db.execute(select(User)).scalars().all()
    return users
    

