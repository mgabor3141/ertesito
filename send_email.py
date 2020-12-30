import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(html, email):
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = email.split(',')
    password = os.getenv("SENDER_PW")

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Változások az Ambulancia Táblázatban [{datetime.now().strftime('%Y-%m-%d %H:00')}]"
    message["From"] = "Táblázat Értesítő"
    message["To"] = ", ".join(receiver_email)

    # Create the plain-text and HTML version of your message
    text = """Kérlek engedélyezd a HTML üzenetek megjelenítését!"""

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
