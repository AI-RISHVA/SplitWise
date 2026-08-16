from app.api.oauth import oauth
from fastapi import  APIRouter ,Depends, Request , HTTPException
from sqlalchemy.orm import Session
from app.db.data import get_session 
from app.api.auth import create_token
from app.models.user import User
from sqlalchemy import select
import random


router = APIRouter()


@router.get("/auth/google/login")
async def google_login(request:Request):
    redirect_url = request.url_for(
        "google_callback"
    )

    return await oauth.google.authorize_redirect(request,redirect_url)


@router.get("/auth/google/callback",name="google_callback")
async def google_callback(request:Request,db: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google.")

    if not userinfo.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google email is not verified.")
    
    google_email = userinfo.get("email")
    google_name = userinfo.get("name", "")
    google_sub = userinfo.get("sub")
    
    if not google_email:
        raise HTTPException(status_code=400, detail="Google account has no email.")

    db_user = db.execute(select(User).where(User.email == google_email)).scalars().first()

    if not db_user:
        base_username = "G" + google_email.split("@")[0].upper()[:15]
        username = base_username
        while db.execute(select(User).where(User.username == username)).scalars().first():
            username = base_username + str(random.randint(100, 999))

        name_parts = google_name.split(" ", 1)
        firstname = name_parts[0] if name_parts else "Google"
        lastname = name_parts[1] if len(name_parts) > 1 else "User"

        db_user = User(
            firstname=firstname,
            lastname=lastname,
            username=username,
            gender=None,
            mobile_no=None,
            email=google_email,
            password=None,
            is_active=True,
            google_id=google_sub,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="This account is deactivated.")

    access_token = create_token({"sub": str(db_user.username)}, is_refresh=False)
    refresh_token = create_token({"sub": str(db_user.username)}, is_refresh=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username
    }