from fastapi import APIRouter ,Depends, HTTPException,status
from app.db.data import get_session
from app.schemas.users import UserOut,UserIn
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List

# database error handling import
from sqlalchemy.exc import IntegrityError


# table import

from app.models.user import User
from app.models.group import Group



# security imports
from app.api.auth import hash_password, verifypass, create_token, verify_token
from fastapi.security import OAuth2PasswordRequestForm




router = APIRouter()
 ### app.inculde_router(user_routes) #a line main file ma lakhvi jethi a file na endpoints tya jova malse





# login api (token genrate with oauth2)

@router.post("/login")
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
        "access_token" :access_token,
        "token_type":"bearer"
    }



@router.post("/register",response_model=UserOut)
async def user_register(signin:UserIn,db: Session = Depends(get_session)):

    statement = select(User).where(User.mobile_no == signin.mobile_no)
    existing_user = db.execute(statement).scalars().first()

    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"Mobile number is already registered"
        )


    

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
    
@router.delete("/delete_account/")
def delete_user_account(
    db: Session = Depends(get_session),
    username: str = Depends(verify_token) ):

    user_statement = select(User).where(User.username == username)
    db_user = db.execute(user_statement).scalars().first()

    if not db_user:
        return {'error': "User not found"}

    all_groups_statement = select(Group)
    all_groups = db.execute(all_groups_statement).scalars().all()

    for group in all_groups:
        if username in group.groupmember:

            updated_members = list(group.groupmember)
            updated_members.remove(username)
            
            group.groupmember = updated_members
            db.add(group) 

    db.delete(db_user)
    
    db.commit()

    return {
        "status": "Success",
        "msg": f"User '{username}' has been deleted, and automatically removed from all groups."
    }


@router.get("/register_view", response_model=List[UserOut])
async def user_view(db: Session = Depends(get_session),username: str = Depends(verify_token)):
    users = db.execute(select(User)).scalars().all()
    return users
    

