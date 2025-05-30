from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import Config


def send_email(
    to: str,
    subject: str,
    title: str,
    body: str,
    button_text: str,
    button_link: str,
):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = Config.EMAIL_USER
    sender_password = Config.EMAIL_PASS

    html_body = f"""
    <html>
      <body style="background: #f5f7ff; font-family: Arial, sans-serif; padding: 24px;">
        <div style="max-width: 600px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px #e0e0e0; padding: 40px; text-align: center;">
          <h2 style="color: #81c6d0; margin-top: 0;">{title}</h2>
          <div style="font-size: 16px; color: #222; margin-bottom: 32px;">
            {body}
          </div>
          <a href="{button_link}" style="display: inline-block; padding: 12px 28px; background: #81c6d0; color: #fff; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px;">
            {button_text}
          </a>
        </div>
        <div style="max-width: 600px; margin: 0 auto; text-align: center;">
          <footer style="font-size: 12px; color: #888;      margin-top: 32px;">
           &copy; {datetime.now().year} Aurelia Labs. All rights reserved.<br>
           Aurelia™ is a trademark of Aurelia Labs.
          </footer>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = f'Aurelia Labs <{sender_email}>'
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to, msg.as_string())
        server.quit()
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Failed to send email: {e}")
