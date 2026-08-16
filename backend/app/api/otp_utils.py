import random
import time

otp_store = {}

OTP_VALID_SECONDS = 300        # 5 minute tak OTP valid rahega
RESEND_COOLDOWN_SECONDS = 60   # 60 second tak dobara resend nahi kar sakte


def generate_otp():
    random_number = random.randint(100000, 999999)
    return str(random_number)


def send_otp(key):
    current_time = time.time()
    existing_otp = otp_store.get(key)

    if existing_otp:
        time_elapsed = current_time - existing_otp["sent_at"]
        if time_elapsed < RESEND_COOLDOWN_SECONDS:
            wait_time = RESEND_COOLDOWN_SECONDS - time_elapsed
            return None, int(wait_time)

    new_otp = generate_otp()
    otp_store[key] = {
        "otp": new_otp,
        "expires_at": current_time + OTP_VALID_SECONDS,
        "sent_at": current_time
    }
    return new_otp, 0


def verify_otp(key, user_input):
    saved_data = otp_store.get(key)

    if not saved_data:
        return False, "OTP was not requested. Please request a new OTP."

    current_time = time.time()
    if current_time > saved_data["expires_at"]:
        del otp_store[key]
        return False, "OTP has expired. Please request a new one."

    if saved_data["otp"] != user_input:
        return False, "Invalid OTP."

    del otp_store[key]
    return True, "OTP verified successfully."