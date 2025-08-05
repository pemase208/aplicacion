import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@aplicacion.com")

def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[str]] = None
) -> bool:
    """
    Send an email to multiple recipients
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        attachments: Optional list of file paths to attach
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = FROM_EMAIL
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject
        
        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        server.sendmail(FROM_EMAIL, to_emails, msg.as_string())
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_welcome_email(email: str, username: str) -> bool:
    """Send welcome email to new user"""
    subject = "Welcome to Aplicacion!"
    body = f"""
    Hello {username},
    
    Welcome to Aplicacion! Your account has been successfully created.
    
    You can now log in to the system using your username: {username}
    
    If you have any questions, please don't hesitate to contact us.
    
    Best regards,
    The Aplicacion Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to Aplicacion!</h2>
            <p>Hello <strong>{username}</strong>,</p>
            <p>Welcome to Aplicacion! Your account has been successfully created.</p>
            <p>You can now log in to the system using your username: <strong>{username}</strong></p>
            <p>If you have any questions, please don't hesitate to contact us.</p>
            <br>
            <p>Best regards,<br>The Aplicacion Team</p>
        </body>
    </html>
    """
    
    return send_email([email], subject, body, html_body)

def send_password_reset_email(email: str, username: str, reset_token: str) -> bool:
    """Send password reset email"""
    subject = "Password Reset Request"
    reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
    
    body = f"""
    Hello {username},
    
    You have requested to reset your password for your Aplicacion account.
    
    Please click the following link to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    The Aplicacion Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello <strong>{username}</strong>,</p>
            <p>You have requested to reset your password for your Aplicacion account.</p>
            <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; display: inline-block;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The Aplicacion Team</p>
        </body>
    </html>
    """
    
    return send_email([email], subject, body, html_body)

def send_notification_email(emails: List[str], subject: str, message: str) -> bool:
    """Send generic notification email"""
    body = f"""
    Hello,
    
    {message}
    
    Best regards,
    The Aplicacion Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Notification</h2>
            <p>{message}</p>
            <br>
            <p>Best regards,<br>The Aplicacion Team</p>
        </body>
    </html>
    """
    
    return send_email(emails, subject, body, html_body)