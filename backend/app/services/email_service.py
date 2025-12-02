"""
Email Service
Handles email sending for password reset and notifications
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from jinja2 import Template

from ..config import settings

logger = logging.getLogger("preklo.email")


class EmailService:
    """
    Email service for sending transactional emails
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@preklo.com")
        self.from_name = os.getenv("FROM_NAME", "Preklo")
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("Email service not configured - emails will be logged instead of sent")
    
    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """
        Send password reset email
        """
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        subject = "Reset Your Preklo Password"
        
        # HTML template for password reset email
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .button { 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #007bff; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Preklo</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>Hello {{ username }},</p>
                    <p>We received a request to reset your password for your Preklo account.</p>
                    <p>Click the button below to reset your password:</p>
                    <a href="{{ reset_url }}" class="button">Reset Password</a>
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p><a href="{{ reset_url }}">{{ reset_url }}</a></p>
                    <p>This link will expire in 1 hour for security reasons.</p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This email was sent from Preklo. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_template = """
        Hello {{ username }},
        
        We received a request to reset your password for your Preklo account.
        
        To reset your password, visit this link:
        {{ reset_url }}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        The Preklo Team
        """
        
        # Render templates
        html_content = Template(html_template).render(
            username=username,
            reset_url=reset_url
        )
        
        text_content = Template(text_template).render(
            username=username,
            reset_url=reset_url
        )
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Send welcome email to new users
        """
        subject = "Welcome to Preklo!"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Preklo</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Preklo!</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ username }}!</h2>
                    <p>Welcome to Preklo, the future of digital payments!</p>
                    <p>Your account has been successfully created. You can now:</p>
                    <ul>
                        <li>Send and receive money instantly</li>
                        <li>Use your @username for easy payments</li>
                        <li>Access your custodial wallet</li>
                        <li>Track your transaction history</li>
                    </ul>
                    <p>If you have any questions, feel free to reach out to our support team.</p>
                </div>
                <div class="footer">
                    <p>Thank you for choosing Preklo!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {username}!
        
        Welcome to Preklo, the future of digital payments!
        
        Your account has been successfully created. You can now:
        - Send and receive money instantly
        - Use your @username for easy payments
        - Access your custodial wallet
        - Track your transaction history
        
        If you have any questions, feel free to reach out to our support team.
        
        Thank you for choosing Preklo!
        """
        
        html_content = Template(html_template).render(username=username)
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def send_sandbox_welcome_email(self, to_email: str, api_key: str, name: str) -> bool:
        """
        Send welcome email to new sandbox users with API key
        """
        dashboard_url = os.getenv("SANDBOX_DASHBOARD_URL", "http://localhost:3000/sandbox")
        quick_start_url = f"{dashboard_url}/quick-start"
        
        subject = "Welcome to Preklo Sandbox - Your API Key"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Preklo Sandbox</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .api-key-box { 
                    background-color: #f8f9fa; 
                    border: 2px dashed #007bff; 
                    padding: 15px; 
                    margin: 20px 0;
                    font-family: monospace;
                    word-break: break-all;
                    text-align: center;
                    font-size: 14px;
                }
                .warning { 
                    background-color: #fff3cd; 
                    border-left: 4px solid #ffc107; 
                    padding: 12px; 
                    margin: 20px 0;
                }
                .button { 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #007bff; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Preklo Sandbox!</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ name }}!</h2>
                    <p>Your sandbox account has been created successfully. You can now start testing Preklo's API.</p>
                    
                    <h3>Your API Key</h3>
                    <div class="api-key-box">{{ api_key }}</div>
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This API key is shown only once. Save it securely now!
                    </div>
                    
                    <h3>What's Next?</h3>
                    <ul>
                        <li>You have 5 pre-configured test accounts ready to use</li>
                        <li>All existing API endpoints work with your sandbox API key</li>
                        <li>Test transactions don't affect production</li>
                    </ul>
                    
                    <a href="{{ dashboard_url }}" class="button">Go to Sandbox Dashboard</a>
                    <a href="{{ quick_start_url }}" class="button" style="background-color: #28a745;">Quick Start Guide</a>
                    
                    <h3>Getting Started</h3>
                    <p>Use your API key in the <code>X-API-Key</code> header for all API requests:</p>
                    <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">curl -H "X-API-Key: {{ api_key }}" https://sandbox-api.preklo.com/api/v1/...</pre>
                </div>
                <div class="footer">
                    <p>This email was sent from Preklo Sandbox. Questions? Reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {name}!
        
        Welcome to Preklo Sandbox!
        
        Your sandbox account has been created successfully. You can now start testing Preklo's API.
        
        YOUR API KEY (SAVE THIS - SHOWN ONLY ONCE):
        {api_key}
        
        ⚠️ Important: This API key is shown only once. Save it securely now!
        
        What's Next?
        - You have 5 pre-configured test accounts ready to use
        - All existing API endpoints work with your sandbox API key
        - Test transactions don't affect production
        
        Dashboard: {dashboard_url}
        Quick Start: {quick_start_url}
        
        Getting Started:
        Use your API key in the X-API-Key header for all API requests:
        
        curl -H "X-API-Key: {api_key}" https://sandbox-api.preklo.com/api/v1/...
        
        Questions? Reply to this email.
        
        Thank you for trying Preklo Sandbox!
        """
        
        html_content = Template(html_template).render(
            name=name,
            api_key=api_key,
            dashboard_url=dashboard_url,
            quick_start_url=quick_start_url
        )
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def _send_email(self, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        Send email using SMTP
        """
        if not self.is_configured:
            # Log email instead of sending in development
            logger.info(f"EMAIL (not sent - not configured):")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content: {text_content}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Password reset email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def test_email_configuration(self) -> bool:
        """
        Test email configuration
        """
        if not self.is_configured:
            logger.warning("Email service not configured")
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            logger.info("Email configuration test successful")
            return True
        except Exception as e:
            logger.error(f"Email configuration test failed: {e}")
            return False


# Global service instance
email_service = EmailService()
