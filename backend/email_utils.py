import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from decouple import config
import logging

# Email configuration
SMTP_SERVER = config("SMTP_SERVER", default="localhost")
SMTP_PORT = config("SMTP_PORT", default=587, cast=int)
SMTP_USERNAME = config("SMTP_USERNAME", default="")
SMTP_PASSWORD = config("SMTP_PASSWORD", default="")
FROM_EMAIL = config("FROM_EMAIL", default="noreply@example.com")

logger = logging.getLogger(__name__)

async def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send an email to one or more recipients"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = FROM_EMAIL
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        
        # Add text body
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)
        
        # Add HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)
        
        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_welcome_email(email: str, username: str) -> bool:
    """Send welcome email to new user"""
    subject = "Welcome to our application!"
    body = f"""
    Hello {username},
    
    Welcome to our application! Your account has been created successfully.
    
    You can now log in and start using our services.
    
    Best regards,
    The Team
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>Welcome {username}!</h2>
        <p>Welcome to our application! Your account has been created successfully.</p>
        <p>You can now log in and start using our services.</p>
        <p>Best regards,<br>The Team</p>
    </body>
    </html>
    """
    
    return await send_email([email], subject, body, html_body)

async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email"""
    subject = "Password Reset Request"
    body = f"""
    Hello,
    
    You have requested a password reset for your account.
    
    Your reset token is: {reset_token}
    
    If you did not request this reset, please ignore this email.
    
    Best regards,
    The Team
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You have requested a password reset for your account.</p>
        <p><strong>Reset Token:</strong> {reset_token}</p>
        <p>If you did not request this reset, please ignore this email.</p>
        <p>Best regards,<br>The Team</p>
    </body>
    </html>
    """
    
    return await send_email([email], subject, body, html_body)

async def send_notification_email(
    email: str,
    subject: str,
    message: str
) -> bool:
    """Send a general notification email"""
    body = f"""
    Hello,
    
    {message}
    
    Best regards,
    The Team
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>{subject}</h2>
        <p>{message}</p>
        <p>Best regards,<br>The Team</p>
    </body>
    </html>
    """
    
    return await send_email([email], subject, body, html_body)