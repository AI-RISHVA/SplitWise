import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger("uvicorn.error")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_email_otp(to_email: str, otp_code: str, purpose: str):
    subject = "Your OTP Code"
    body = f"Your OTP is: {otp_code}\nThis code is valid for 5 minutes.\nPurpose: {purpose}"

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        logger.info(f"OTP Email successfully sent to {to_email}")  # <-- Success Log

    except Exception as error:
        logger.error(f"Failed to send email to {to_email}: {error}", exc_info=True)


def send_sms_otp(to_mobile: str, otp_code: str, purpose: str):
    logger.info(f"[SMS simulation] To: {to_mobile} | Purpose: {purpose} | OTP: {otp_code}")
    # TODO: real SMS gateway (Twilio / MSG91) yaha aayega