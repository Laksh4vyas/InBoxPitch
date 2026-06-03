from dotenv import load_dotenv

load_dotenv()

import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def send_email(receiver_email, subject, body, resume_path):

    import os

    sender_email = os.getenv("EMAIL_ADDRESS")

    sender_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart()

    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    # Attach Resume PDF
    with open(resume_path, "rb") as file:

        pdf_attachment = MIMEApplication(file.read(), _subtype="pdf")

        pdf_attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename="Laksh_Vyas_Resume.pdf"
        )

        message.attach(pdf_attachment)

    # SMTP Server
    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(sender_email, sender_password)

    server.send_message(message)

    server.quit()
