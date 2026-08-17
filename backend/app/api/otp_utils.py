import random
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.otp import OTPStore # Model import kiya

OTP_VALID_SECONDS = 300        
RESEND_COOLDOWN_SECONDS = 60   

def generate_otp():
    return str(random.randint(100000, 999999))


# 1. SEND OTP FUNCTION (Async)
async def send_otp(db: AsyncSession, key: str):
    current_time = time.time()
    
    # Check karein kya pehle se OTP table me exist karta hai
    result = await db.execute(select(OTPStore).where(OTPStore.key == key))
    existing_otp = result.scalars().first()

    if existing_otp:
        time_elapsed = current_time - existing_otp.sent_at
        if time_elapsed < RESEND_COOLDOWN_SECONDS:
            wait_time = RESEND_COOLDOWN_SECONDS - time_elapsed
            return None, int(wait_time)
        
        # Agar cooldown khatam ho gaya hai, toh purana record delete kar dete hain
        await db.delete(existing_otp)

    new_otp = generate_otp()
    
    # Naya OTP record database object me banayein
    db_otp = OTPStore(
        key=key,
        otp=new_otp,
        expires_at=current_time + OTP_VALID_SECONDS,
        sent_at=current_time
    )
    db.add(db_otp)
    await db.commit() # DB me save kiya
    
    return new_otp, 0


# 2. VERIFY OTP FUNCTION (Async)
async def verify_otp(db: AsyncSession, key: str, user_input: str):
    # DB se record nikalein
    result = await db.execute(select(OTPStore).where(OTPStore.key == key))
    saved_data = result.scalars().first()

    if not saved_data:
        return False, "OTP was not requested. Please request a new OTP."

    current_time = time.time()
    
    # Check expire hua ya nahi
    if current_time > saved_data.expires_at:
        await db.delete(saved_data) # Expire ho gaya toh delete karein
        await db.commit()
        return False, "OTP has expired. Please request a new one."

    # Check OTP sahi hai ya nahi
    if saved_data.otp != user_input:
        return False, "Invalid OTP."

    # OTP sahi hai, toh verify hone ke baad DB se delete karein
    await db.delete(saved_data)
    await db.commit()
    
    return True, "OTP verified successfully."
