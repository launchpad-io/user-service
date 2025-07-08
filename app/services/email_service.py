# app/services/email_service.py - Email Service with Debug Logging
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import ssl
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration from settings
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.MAIL_FROM
        self.from_name = settings.MAIL_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        
        # Log configuration (without password)
        logger.info(f"Email Service Configuration:")
        logger.info(f"  SMTP Server: {self.smtp_server}")
        logger.info(f"  SMTP Port: {self.smtp_port}")
        logger.info(f"  Username: {self.username}")
        logger.info(f"  From Email: {self.from_email}")
        logger.info(f"  Use TLS: {self.use_tls}")
        logger.info(f"  Password configured: {'Yes' if self.password else 'No'}")
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email using SMTP with detailed logging"""
        try:
            logger.info(f"📧 Attempting to send email to: {to_email}")
            logger.info(f"   Subject: {subject}")
            
            # Check if email is enabled
            if not settings.MAIL_ENABLED:
                logger.warning("❌ Email sending is disabled in settings")
                return False
            
            # Check if password is configured
            if not self.password:
                logger.error("❌ SMTP password not configured")
                return False
            
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
            
            # Connect to server and send email
            logger.info(f"📧 Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            if self.smtp_port == 465:
                # SSL connection
                logger.info("   Using SSL connection")
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    logger.info("   Logging in...")
                    server.login(self.username, self.password)
                    logger.info("   Sending email...")
                    server.sendmail(self.from_email, to_email, message.as_string())
            else:
                # STARTTLS connection
                logger.info("   Using STARTTLS connection")
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        logger.info("   Starting TLS...")
                        server.starttls()
                    logger.info("   Logging in...")
                    server.login(self.username, self.password)
                    logger.info("   Sending email...")
                    server.sendmail(self.from_email, to_email, message.as_string())
                
            logger.info(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {str(e)}")
            logger.error("   Check your email username and password")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ Failed to connect to SMTP server: {str(e)}")
            logger.error(f"   Check server: {self.smtp_server} and port: {self.smtp_port}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_verification_email(self, to_email: str, username: str, verification_token: str, frontend_url: str = "http://localhost:3000") -> bool:
        """Send email verification email"""
        
        logger.info(f"📧 Preparing verification email for: {to_email}")
        logger.info(f"   Username: {username}")
        logger.info(f"   Token: {verification_token[:8]}...")
        logger.info(f"   Frontend URL: {frontend_url}")
        
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
                .token-box {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 14px; text-align: center; margin: 20px 0; word-break: break-all; }}
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
                    
                    <p><strong>Option 2:</strong> Copy and paste this verification token on the verification page:</p>
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