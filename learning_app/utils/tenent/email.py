import smtplib
from email.message import EmailMessage
from utils.tenent.email_template import otp_email_template

SMTP_EMAIL = "digidense.dev@gmail.com"
SMTP_PASSWORD = "hzipfqwpmnxmjwwv"

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    html_content = otp_email_template(otp)
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP("smtp.gmail.com", 587):
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()



################################
### outlook mail
############################
# import smtplib
# from email.message import EmailMessage
# from utils.tenent.email_template import otp_email_template

# SMTP_EMAIL = "no-reply@digidense.com"
# SMTP_PASSWORD = "OUTLOOK_APP_PASSWORD"

# def send_otp_email(to_email: str, otp: str):
#     msg = EmailMessage()
#     msg["Subject"] = "Your verification code"
#     msg["From"] = SMTP_EMAIL
#     msg["To"] = to_email

#     msg.add_alternative(
#         otp_email_template(otp),
#         subtype="html"
#     )

#     with smtplib.SMTP("smtp.office365.com", 587) as server:
#         server.starttls()
#         server.login(SMTP_EMAIL, SMTP_PASSWORD)
#         server.send_message(msg)

