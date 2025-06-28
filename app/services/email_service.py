# app/services/email_service.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.mail_from = settings.MAIL_FROM
        self.mail_from_name = settings.MAIL_FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
        self.enabled = settings.MAIL_ENABLED
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email using SMTP"""
        if not self.enabled:
            logger.warning("Email service is disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.mail_from_name} <{self.mail_from}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
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
        """Send email verification link with professional enterprise template"""
        verification_url = f"{self.frontend_url}/auth/verify-email?token={token}"
        
        subject = "Welcome to LaunchPAID - Please Verify Your Email"
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <!--[if mso]>
            <noscript>
                <xml>
                    <o:OfficeDocumentSettings>
                        <o:PixelsPerInch>96</o:PixelsPerInch>
                    </o:OfficeDocumentSettings>
                </xml>
            </noscript>
            <![endif]-->
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f3f4f6;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                            <!-- Logo Header -->
                            <tr>
                                <td align="center" style="padding: 48px 0 24px 0;">
                                    <div style="display: inline-block;">
                                        <h1 style="margin: 0; font-size: 32px; font-weight: 700; color: #9333ea; letter-spacing: -0.5px;">
                                            LaunchPAID
                                        </h1>
                                        <p style="margin: 8px 0 0 0; font-size: 14px; color: #6b7280; font-weight: 500;">
                                            The Premier TikTok Influencer Marketing Platform
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Welcome Section -->
                            <tr>
                                <td style="padding: 0 48px;">
                                    <h2 style="margin: 0 0 24px 0; font-size: 28px; font-weight: 600; color: #111827; text-align: center;">
                                        Welcome to LaunchPAID, {full_name or 'there'}!
                                    </h2>
                                    <p style="margin: 0 0 32px 0; font-size: 16px; line-height: 24px; color: #4b5563; text-align: center;">
                                        Thank you for joining our exclusive network of brands and creators. 
                                        To complete your registration and access your account, please verify your email address.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- CTA Button -->
                            <tr>
                                <td align="center" style="padding: 0 48px 40px 48px;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                        <tr>
                                            <td align="center" style="border-radius: 6px; background-color: #9333ea;">
                                                <a href="{verification_url}" 
                                                   target="_blank" 
                                                   style="display: inline-block; padding: 16px 32px; font-size: 16px; font-weight: 600; 
                                                          color: #ffffff; text-decoration: none; border-radius: 6px;">
                                                    Verify Email Address
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Security Notice -->
                            <tr>
                                <td style="padding: 0 48px 40px 48px;">
                                    <div style="background-color: #f9fafb; border-radius: 6px; padding: 16px; border-left: 4px solid #9333ea;">
                                        <p style="margin: 0; font-size: 14px; color: #6b7280;">
                                            <strong style="color: #4b5563;">Security Notice:</strong> 
                                            This verification link will expire in 24 hours. If you did not create an account with LaunchPAID, 
                                            please disregard this email.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- What's Next Section -->
                            <tr>
                                <td style="padding: 0 48px 48px 48px;">
                                    <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #111827;">
                                        What happens next?
                                    </h3>
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td valign="top" style="padding-right: 12px;">
                                                <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #ede9fe; 
                                                            color: #9333ea; text-align: center; line-height: 24px; font-weight: 600; font-size: 14px;">
                                                    1
                                                </div>
                                            </td>
                                            <td style="padding-bottom: 16px;">
                                                <p style="margin: 0; font-size: 14px; color: #4b5563;">
                                                    Click the verification button to confirm your email address
                                                </p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" style="padding-right: 12px;">
                                                <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #ede9fe; 
                                                            color: #9333ea; text-align: center; line-height: 24px; font-weight: 600; font-size: 14px;">
                                                    2
                                                </div>
                                            </td>
                                            <td style="padding-bottom: 16px;">
                                                <p style="margin: 0; font-size: 14px; color: #4b5563;">
                                                    Complete your profile to maximize your opportunities
                                                </p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" style="padding-right: 12px;">
                                                <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #ede9fe; 
                                                            color: #9333ea; text-align: center; line-height: 24px; font-weight: 600; font-size: 14px;">
                                                    3
                                                </div>
                                            </td>
                                            <td>
                                                <p style="margin: 0; font-size: 14px; color: #4b5563;">
                                                    Start connecting with brands and creators immediately
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f9fafb; padding: 32px 48px; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td align="center">
                                                <p style="margin: 0 0 8px 0; font-size: 12px; color: #6b7280;">
                                                    © 2024 LaunchPAID. All rights reserved.
                                                </p>
                                                <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                                                    LaunchPAID is a product of Novanex Ventures
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to LaunchPAID, {full_name or 'there'}!
        
        Thank you for joining our exclusive network of brands and creators.
        
        To complete your registration and access your account, please verify your email address by clicking the link below:
        
        {verification_url}
        
        What happens next?
        1. Click the verification link to confirm your email address
        2. Complete your profile to maximize your opportunities
        3. Start connecting with brands and creators immediately
        
        Security Notice: This verification link will expire in 24 hours. If you did not create an account with LaunchPAID, please disregard this email.
        
        © 2024 LaunchPAID. All rights reserved.
        LaunchPAID is a product of Novanex Ventures
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_welcome_email(self, to_email: str, full_name: str, role: str) -> bool:
        """Send welcome email after successful verification"""
        subject = "Welcome to LaunchPAID! 🎉"
        
        role_specific_content = {
            "creator": "Start showcasing your TikTok content and connect with brands looking for authentic creators like you.",
            "brand": "Discover talented TikTok creators and launch impactful influencer marketing campaigns.",
            "agency": "Manage your clients' campaigns and connect with top TikTok creators all in one place."
        }
        
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
            <!-- Header -->
            <div style="background-color: #9333ea; padding: 40px 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">LaunchPAID</h1>
            </div>
            
            <!-- Body -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #1a1a1a; font-size: 24px; margin-bottom: 20px;">You're all set, {full_name}! 🚀</h2>
                
                <p style="color: #4b5563; font-size: 16px; line-height: 24px; margin-bottom: 30px;">
                    Your email has been verified and your LaunchPAID account is now active. 
                    {role_specific_content.get(role.lower(), "Start exploring the platform and make meaningful connections.")}
                </p>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{self.frontend_url}/dashboard" 
                       style="background-color: #9333ea; color: white; padding: 14px 35px; 
                              text-decoration: none; border-radius: 8px; display: inline-block;
                              font-weight: 600; font-size: 16px;">
                        Go to Dashboard
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    © 2024 LaunchPAID. All rights reserved.
                </p>
            </div>
        </div>
        """
        
        text_body = f"""
        You're all set, {full_name}!
        
        Your email has been verified and your LaunchPAID account is now active.
        
        {role_specific_content.get(role.lower(), "Start exploring the platform and make meaningful connections.")}
        
        Go to your dashboard: {self.frontend_url}/dashboard
        
        © 2024 LaunchPAID
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_password_reset_email(self, to_email: str, full_name: str, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.frontend_url}/auth/reset-password?token={token}"
        
        subject = "Reset your LaunchPAID password"
        
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
            <!-- Header -->
            <div style="background-color: #9333ea; padding: 40px 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">LaunchPAID</h1>
            </div>
            
            <!-- Body -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #1a1a1a; font-size: 24px; margin-bottom: 20px;">Password Reset Request</h2>
                
                <p style="color: #4b5563; font-size: 16px; line-height: 24px; margin-bottom: 30px;">
                    Hi {full_name or 'there'},<br><br>
                    We received a request to reset your password. Click the button below to create a new password.
                </p>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #9333ea; color: white; padding: 14px 35px; 
                              text-decoration: none; border-radius: 8px; display: inline-block;
                              font-weight: 600; font-size: 16px;">
                        Reset Password
                    </a>
                </div>
                
                <div style="background-color: #fafafa; border-radius: 6px; padding: 15px; margin: 30px 0;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        Or copy and paste this link:
                    </p>
                    <p style="color: #9333ea; font-size: 12px; word-break: break-all; margin: 10px 0 0 0;">
                        {reset_url}
                    </p>
                </div>
                
                <div style="border-top: 1px solid #e5e7eb; margin-top: 40px; padding-top: 20px;">
                    <p style="color: #9ca3af; font-size: 12px; line-height: 18px; margin: 0;">
                        This link will expire in <strong>1 hour</strong> for security reasons.<br>
                        If you didn't request a password reset, you can safely ignore this email.
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    © 2024 LaunchPAID. All rights reserved.
                </p>
            </div>
        </div>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hi {full_name or 'there'},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        © 2025 LaunchPAID
        """
        
        return self._send_email(to_email, subject, html_body, text_body)


# Create singleton instance
email_service = EmailService()