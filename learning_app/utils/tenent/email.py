import smtplib
from email.message import EmailMessage

SMTP_EMAIL = "akhilmony01@gmail.com"
SMTP_PASSWORD = "ylegnnhzhrpqytbt"

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your Login OTP"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    msg.set_content(f"""
Your OTP to login is:

{otp}

If you did not request this, ignore this email.
""")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
