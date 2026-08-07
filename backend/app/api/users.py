# ######    EMAIL UPDATE BAKI THROUGH OTP, FORGET PASSWORD BAKI , PHONE NUMBER UPDATE THROUGH OTP


from fastapi import APIRouter ,Depends, HTTPException,status
from app.db.data import get_session
from app.schemas.users import UserOut,UserIn , ProfileUpdate, PasswordChange
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List

# database error handling import
from sqlalchemy.exc import IntegrityError


# table import

from app.models.user import User
from app.models.group import Group

# security imports
from app.api.auth import hash_password, verifypass, create_token, verify_token, oauth2_scheme
from app.models.token_blacklist import BlacklistedToken
from fastapi.security import OAuth2PasswordRequestForm




router = APIRouter()
 ### app.inculde_router(user_routes) #a line main file ma lakhvi jethi a file na endpoints tya jova malse






# ..........................................................................

@router.post("/register",response_model=UserOut)
async def user_register(signin:UserIn,db: Session = Depends(get_session)):

    existing_user = db.execute(select(User).where(User.username == signin.username)).scalars().first()
    existing_email = db.execute(select(User).where(User.email == signin.email)).scalars().first()
    existing_mobile_no = db.execute(select(User).where(User.mobile_no == signin.mobile_no)).scalars().first()
    
    
    if existing_user:
        raise HTTPException(status_code=400, detail=f"Username is already registered")
    if existing_email:
            raise HTTPException(status_code=400, detail=f"email is already registered")
    if existing_mobile_no:
            raise HTTPException(status_code=400, detail=f"mobile is already registered")

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
        db.add(db_user) 
        
        db.commit() 
        
        db.refresh(db_user)  #data ne refresh kare jethi koi id bani hoy to db ma store thay
    
        return db_user

    
    except IntegrityError as e:
        db.rollback() # if koi error avse to db rollback kare(atle ke "undo" kare)
        error_msg = str(e.orig)
        
        if "user.username" in error_msg or "user.username" in error_msg:
            detail_msg = "Username already exists. Please choose a unique username."
        elif "user.email" in error_msg or "user.email" in error_msg:
            detail_msg = "Email is already registered. Please use another email."
        else:
            detail_msg = "This user data already exists."

        # 3. Server crash karva na badle 400 Error batave
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )


# ..........................................................................

@router.post("/login")
def login(form_data :OAuth2PasswordRequestForm=Depends(),db: Session = Depends(get_session)
):
    # user = db.execute(select(User).where(User.username == form_data.username)).scalars().first()
    db_user = db.execute(select(User).where(User.username == form_data.username, User.is_active == True)).scalars().first()
 
    if not db_user or not verifypass(form_data.password,db_user.password):
        raise HTTPException(
            status_code=400,
            detail="invalid username & password"
        )

    # 1. Access Token (Short-lived)
    access_token = create_token({"sub":  str(db_user.id)}, is_refresh=False)
    
    # 2. Refresh Token (Long-lived)
    refresh_token = create_token({"sub":  str(db_user.id)}, is_refresh=True)



    return {
        "access_token":access_token,
        "refresh_token":refresh_token,
        "token_type":"bearer"
    }

#  ..........................................................................

@router.put("/update_profile/")
def update_profile(profile_data: ProfileUpdate, db: Session = Depends(get_session), username: str = Depends(verify_token)):
    db_user = db.execute(select(User).where(User.username == username)).scalars().first()
    
    
    if not db_user:
        return {'error': "User not found"}
    
    if profile_data.firstname:
        db_user.firstname = profile_data.firstname
    if profile_data.lastname:
        db_user.lastname = profile_data.lastname
    if profile_data.gender:
        db_user.gender = profile_data.gender


    if profile_data.email:
        existing_email = db.execute(select(User).where(User.email == profile_data.email, User.username != username)).scalars().first()

        if existing_email:
            raise HTTPException(status_code=400, detail="This email is already registered ")
        db_user.email = profile_data.email

    if profile_data.mobile_no:
        existing_mobile = db.execute(
            select(User).where(User.mobile_no == profile_data.mobile_no, User.username != username)
        ).scalars().first()
        if existing_mobile:
            raise HTTPException(status_code=400, detail="This mobile number is already registered with another user.")
        db_user.mobile_no = profile_data.mobile_no


    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This email is already registered with another user.")

# ...................................................................

@router.put("/change_password/")
def change_password(passdata: PasswordChange, db: Session = Depends(get_session), username: str = Depends(verify_token)):
    db_user = db.execute(select(User).where(User.username == username)).scalars().first()
    if not db_user:
        return {'error': "User not found"}
    
    if passdata.new_password == passdata.old_password:
            raise HTTPException(status_code=400, detail="your new password is match your current password, please add diffrent password.")
    
    if not verifypass(passdata.old_password, db_user.password):
        raise HTTPException(status_code=400, detail="The old password you entered is incorrect.")

    if not passdata.new_password == passdata.confirm_password:
        raise HTTPException(status_code=400, detail="new password entered is not match with confirm password.")
    
        
    # Naya password hash karke save karo
    db_user.password = hash_password(passdata.new_password)
    db.add(db_user)
    db.commit()
    return {"status": "Success", "msg": "Password changed successfully! Keep it secure."}

# ...................................................................
@router.get("/me", response_model=UserOut)
def get_user_profile(db: Session = Depends(get_session), username: str = Depends(verify_token)):
    db_user = db.execute(select(User).where(User.username == username)).scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return db_user

# ...................................................................
@router.post("/logout/")
def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
    username: str = Depends(verify_token)
):
    # e token blacklist table ma nakhi didhu have e fari use no thy atle
    db_token = BlacklistedToken(token=token)
    db.add(db_token)
    db.commit()
    return {"status": "Success", "msg": f"Session closed. User '{username}' logged out successfully."}
# ..........................................................................


@router.delete("/delete_account/")
def delete_user_account(db: Session = Depends(get_session),username: str = Depends(verify_token) ):
    
    db_user = db.execute(select(User).where(User.username == username)).scalars().first()
    
    # db_user = db.execute(select(User).where(User.username == username, User.is_active == True)).scalars().first()  #a user soft delete mate che


    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    all_groups = db.execute(select(Group)).scalars().all()

    for i in all_groups:
        if username in i.groupmember:

            updated_members = list(i.groupmember)
            updated_members.remove(username)
            
            i.groupmember = updated_members
            db.add(i) 

    db.delete(db_user) #a perment delte mate che

    # db_user.is_active = False  #ansa thi khsali deactive thase
    # db.add(db_user) 

    db.commit()


    return {
        "status": "Success",
        "msg": f"User '{username}' has been deleted, and automatically removed from all groups."
    }


