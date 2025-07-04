# app/services/email_service.py - Email Service Implementation
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import ssl

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration based on your settings
        self.smtp_server = "mail.bytecraftsoft.com"
        self.smtp_port = 465  # SSL port
        self.username = "launchpaid@bytecraftsoft.com"
        self.password = "0E%*)t(6[!A,84g^"
        self.from_email = "launchpaid@bytecraftsoft.com"
        self.from_name = "LaunchPAID Team"
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Create text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server and send email
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, message.as_string())
                
            logger.info(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, to_email: str, username: str, verification_token: str, frontend_url: str = "http://localhost:3000") -> bool:
        """Send email verification email"""
        
        verification_url = f"{frontend_url}/auth/verify-email?token={verification_token}&email={to_email}"
        
        subject = "Verify Your LaunchPAID Account"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: bold; color: #3b82f6; margin-bottom: 10px; }}
                .title {{ font-size: 24px; color: #333; margin-bottom: 20px; }}
                .content {{ color: #555; margin-bottom: 30px; }}
                .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .button:hover {{ background: #2563eb; }}
                .token-box {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 18px; text-align: center; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚀 LaunchPAID</div>
                    <h1 class="title">Verify Your Email Address</h1>
                </div>
                
                <div class="content">
                    <p>Hi {username},</p>
                    
                    <p>Welcome to LaunchPAID! To complete your account setup, please verify your email address.</p>
                    
                    <p><strong>Option 1:</strong> Click the button below to verify automatically:</p>
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p><strong>Option 2:</strong> Copy and paste this verification token:</p>
                    <div class="token-box">
                        {verification_token}
                    </div>
                    
                    <p>This verification link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you didn't create an account with LaunchPAID, please ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>Best regards,<br>The LaunchPAID Team</p>
                    <p><em>This is an automated email. Please do not reply to this message.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Hi {username},
        
        Welcome to LaunchPAID! To complete your account setup, please verify your email address.
        
        Verification Token: {verification_token}
        
        Or click this link: {verification_url}
        
        This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with LaunchPAID, please ignore this email.
        
        Best regards,
        The LaunchPAID Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, username: str, reset_token: str, frontend_url: str = "http://localhost:3000") -> bool:
        """Send password reset email"""
        
        reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}&email={to_email}"
        
        subject = "Reset Your LaunchPAID Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: bold; color: #3b82f6; margin-bottom: 10px; }}
                .title {{ font-size: 24px; color: #333; margin-bottom: 20px; }}
                .content {{ color: #555; margin-bottom: 30px; }}
                .button {{ display: inline-block; background: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .button:hover {{ background: #b91c1c; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚀 LaunchPAID</div>
                    <h1 class="title">Reset Your Password</h1>
                </div>
                
                <div class="content">
                    <p>Hi {username},</p>
                    
                    <p>We received a request to reset your password for your LaunchPAID account.</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p>This password reset link will expire in 1 hour for security reasons.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                </div>
                
                <div class="footer">
                    <p>Best regards,<br>The LaunchPAID Team</p>
                    <p><em>This is an automated email. Please do not reply to this message.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

# Create global instance
email_service = EmailService()