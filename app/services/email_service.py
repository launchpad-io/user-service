# app/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.enabled = settings.MAIL_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.mail_from = settings.MAIL_FROM
        self.mail_from_name = settings.MAIL_FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP.
        Returns True if successful, False otherwise.
        """
        if not self.enabled:
            logger.info(f"Email sending disabled. Would send: {subject} to {to_email}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.mail_from_name} <{self.mail_from}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, to_email: str, full_name: str, token: str) -> bool:
        """Send email verification link"""
        verification_url = f"{self.frontend_url}/auth/verify-email?token={token}"
        
        subject = "Verify your LaunchPAID account"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #9333ea;">Welcome to LaunchPAID!</h2>
            <p>Hi {full_name or 'there'},</p>
            <p>Thanks for signing up! Please verify your email address to get started.</p>
            <div style="margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #9333ea; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                If you didn't create an account, you can safely ignore this email.
            </p>
        </div>
        """
        
        text_body = f"""
        Welcome to LaunchPAID!
        
        Hi {full_name or 'there'},
        
        Thanks for signing up! Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, you can safely ignore this email.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_password_reset_email(self, to_email: str, full_name: str, token: str) -> bool:
        """Send password reset link"""
        reset_url = f"{self.frontend_url}/auth/reset-password?token={token}"
        
        subject = "Reset your LaunchPAID password"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #9333ea;">Password Reset Request</h2>
            <p>Hi {full_name or 'there'},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <div style="margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #9333ea; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{reset_url}</p>
            <p>This link will expire in 1 hour for security reasons.</p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                If you didn't request a password reset, you can safely ignore this email.
                Your password won't be changed.
            </p>
        </div>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hi {full_name or 'there'},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, you can safely ignore this email.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_welcome_email(self, to_email: str, full_name: str, role: str) -> bool:
        """Send welcome email after successful verification"""
        dashboard_url = f"{self.frontend_url}/dashboard"
        
        subject = "Welcome to LaunchPAID! 🚀"
        
        role_specific_content = {
            "creator": "Start connecting with brands and monetize your TikTok presence.",
            "agency": "Manage your creators and campaigns all in one place.",
            "brand": "Discover and collaborate with top-performing creators."
        }
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #9333ea;">Welcome to LaunchPAID, {full_name}! 🎉</h2>
            <p>Your email has been verified and your account is now active.</p>
            <p>{role_specific_content.get(role, 'Start exploring LaunchPAID today.')}</p>
            <div style="margin: 30px 0;">
                <a href="{dashboard_url}" 
                   style="background-color: #9333ea; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Go to Dashboard
                </a>
            </div>
            <p>Need help getting started? Check out our resources:</p>
            <ul style="color: #666;">
                <li>Getting Started Guide</li>
                <li>FAQ</li>
                <li>Contact Support</li>
            </ul>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                Powered by Novanex
            </p>
        </div>
        """
        
        return self._send_email(to_email, subject, html_body)


# Create a singleton instance
email_service = EmailService()