"""
Email Provider Abstraction Layer
Supports SMTP (Gmail) and Resend HTTP API for flexible email delivery
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass
    
    @abstractmethod
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "registration") -> bool:
        """Send OTP email"""
        pass
    
    @abstractmethod
    def send_newsletter_confirmation(self, subscriber_email: str) -> bool:
        """Send newsletter confirmation email"""
        pass
    
    @abstractmethod
    def send_contact_email(self, contact_data: Dict[str, str]) -> bool:
        """Send contact form email"""
        pass


class SMTPEmailProvider(EmailProvider):
    """SMTP-based email provider (Gmail)"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER") or os.getenv("SENDER_EMAIL")
        configured_sender = os.getenv("SMTP_FROM_EMAIL") or self.smtp_user
        # Gmail commonly rejects arbitrary From addresses; default to authenticated account.
        if self.smtp_user and "gmail" in self.smtp_server.lower():
            self.sender_email = self.smtp_user
        else:
            self.sender_email = configured_sender
        self.sender_name = os.getenv("SMTP_FROM_NAME", "CareerLens")
        self.sender_password = os.getenv("SMTP_PASSWORD") or os.getenv("SENDER_PASSWORD")
        self.contact_form_email = os.getenv("CONTACT_FORM_EMAIL", self.sender_email or self.smtp_user or "")

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.sender_password)
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "registration") -> bool:
        """Send OTP via SMTP"""
        if not self.is_configured():
            print("OTP email failed: SMTP_USER/SMTP_PASSWORD not configured")
            return False
        
        try:
            subject = {
                "registration": "Verify Your Email - CareerLens",
                "login_2fa": "Login Verification Code - CareerLens",
                "password_reset": "Password Reset Code - CareerLens"
            }.get(purpose, "Verification Code - CareerLens")
            
            body = self._get_otp_email_body(otp, purpose)
            
            # Use 'related' to hold inline images
            message = MIMEMultipart("related")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Alternative container holds the html
            msg_alternative = MIMEMultipart("alternative")
            message.attach(msg_alternative)
            msg_alternative.attach(MIMEText(body, "html"))
            
            # Attach CID Image (Logo)
            logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "careerlens-logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name="careerlens-logo.png")
                image.add_header("Content-ID", "<careerlens_logo>")
                image.add_header("Content-Disposition", "inline")
                message.attach(image)
            else:
                print(f"Warning: Logo not found at {logo_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            print(f"SMTP: OTP email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"SMTP: Failed to send OTP email: {str(e)}")
            return False
    
    def send_newsletter_confirmation(self, subscriber_email: str) -> bool:
        """Send newsletter confirmation via SMTP"""
        if not self.is_configured():
            print("Error: SMTP_USER/SMTP_PASSWORD not configured. Newsletter emails cannot be sent.")
            return False
        
        try:
            msg = MIMEMultipart("related")
            msg["Subject"] = "Welcome to the CareerLens Newsletter! 🎉"
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = subscriber_email

            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)
            
            html_body = self._get_newsletter_email_body()
            msg_alternative.attach(MIMEText(html_body, "html"))
            
            # Attach logo
            logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "careerlens-logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name="careerlens-logo.png")
                image.add_header("Content-ID", "<careerlens_logo>")
                image.add_header("Content-Disposition", "inline")
                msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.sender_password)
                server.sendmail(self.sender_email, subscriber_email, msg.as_string())
            
            print(f"SMTP: Newsletter confirmation sent to {subscriber_email}")
            return True
        except Exception as e:
            print(f"SMTP: Failed to send newsletter email: {str(e)}")
            return False
    
    def send_contact_email(self, contact_data: Dict[str, str]) -> bool:
        """Send contact form email via SMTP"""
        if not self.is_configured():
            print("Error: SMTP not configured. Contact emails cannot be sent.")
            return False
        
        try:
            recipient_email = self.contact_form_email
            name = contact_data.get("name", "")
            subject = contact_data.get("subject", "Contact Form Submission")
            sender_email = contact_data.get("email", "")
            
            msg = MIMEMultipart("related")
            msg["Subject"] = f"Contact Form Received - {subject}"
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = recipient_email
            if sender_email:
              msg["Reply-To"] = sender_email

            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)
            
            html_body = self._get_contact_email_body(name, subject)
            msg_alternative.attach(MIMEText(html_body, "html"))
            
            # Attach logo
            logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "careerlens-logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name="careerlens-logo.png")
                image.add_header("Content-ID", "<careerlens_logo>")
                image.add_header("Content-Disposition", "inline")
                msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
            
            print(f"SMTP: Contact email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"SMTP: Failed to send contact email: {str(e)}")
            return False
    
    def _get_otp_email_body(self, otp: str, purpose: str) -> str:
        """Generate OTP email HTML body"""
        title = {
            "registration": "Email Verification",
            "login_2fa": "Two-Step Authentication",
            "password_reset": "Password Reset Request"
        }.get(purpose, "Verification Code")
        
        message = {
            "registration": "Welcome to CareerLens! Please verify your email address to complete your registration and start exploring career opportunities.",
            "login_2fa": "A sign-in attempt requires further verification. Enter the code below to securely access your account.",
            "password_reset": "We received a request to reset your CareerLens password. Use the verification code below to securely create a new password."
        }.get(purpose, "Use this code to verify your request.")
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="cid:careerlens_logo" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        {title}
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        {message}
                      </p>
                      
                      <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0f9ff; border: 1px solid rgba(0, 194, 203, 0.3); border-radius: 12px; margin-bottom: 30px;">
                        <tr>
                          <td align="center" style="padding: 24px;">
                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #00C2CB; display: block;">
                              {otp}
                            </span>
                          </td>
                        </tr>
                      </table>
                      
                      <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-align: center;">
                        This code will securely expire in <strong style="color: #475569;">10 minutes</strong>.
                      </p>
                      
                      <p style="margin: 0; font-size: 14px; color: #ef4444; font-weight: 500; text-align: center;">
                        Please do not share this code with anyone.
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you did not request this email, there is nothing you need to do. Because this is a security notification, you may still receive it even if you have opted out of marketing emails.
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''
    
    def _get_newsletter_email_body(self) -> str:
        """Generate newsletter confirmation email body"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Welcome to CareerLens Newsletter</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="cid:careerlens_logo" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        Welcome to the CareerLens Newsletter!
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        Thank you for subscribing! You will now receive the latest updates on AI-powered career insights, new platform features, and tips for students and recruiters.
                      </p>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 14px; color: #64748b; text-align: center; line-height: 1.8;">
                        <strong style="color: #0f172a;">What to expect:</strong><br/>
                        🚀 AI-powered career insights and industry trends<br/>
                        ✨ New platform features and improvements<br/>
                        📊 Tips for leveraging data-driven career analysis<br/>
                        💡 Exclusive insights for students and recruiters
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you wish to unsubscribe or manage your preferences, please contact us at support@careerlens.in
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''
    
    def _get_contact_email_body(self, name: str, subject: str) -> str:
        """Generate contact form confirmation email body"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>We Received Your Message</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="cid:careerlens_logo" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        We Received Your Message
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        Hi {name},<br/>Thank you for reaching out to us! We have received your message regarding <strong>{subject}</strong> and will get back to you as soon as possible.
                      </p>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 14px; color: #64748b; text-align: center;">
                        Our team typically responds within 24-48 business hours. In the meantime, feel free to explore more features on our platform or check our documentation.
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you have any urgent concerns, please contact us directly at support@careerlens.in
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''


class ResendEmailProvider(EmailProvider):
    """Resend HTTP API-based email provider"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY", "")
        self.sender_email = os.getenv("SMTP_FROM_EMAIL", "noreply@careerlens.in")
        self.sender_name = os.getenv("SMTP_FROM_NAME", "CareerLens")
        self.from_header = f"{self.sender_name} <{self.sender_email}>"
        self.api_url = "https://api.resend.com/emails"
        self.contact_form_email = os.getenv("CONTACT_FORM_EMAIL", self.sender_email)
        self.logo_url = os.getenv("EMAIL_LOGO_URL", "https://www.careerlens.in/careerlens-logo.png")
    
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())
    
    def _send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Send email via Resend API"""
        if not self.is_configured():
            print("Resend: API key not configured")
            return False
        
        try:
            api_headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": self.from_header,
                "to": [to],
                "subject": subject,
                "html": html
            }
            if text:
                payload["text"] = text
            if reply_to:
                payload["reply_to"] = reply_to
            if headers:
                payload["headers"] = headers
            
            response = requests.post(self.api_url, json=payload, headers=api_headers, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"Resend: Email sent to {to} (ID: {response.json().get('id', 'unknown')})")
                return True
            else:
                error_msg = response.text
                try:
                    error_msg = response.json().get("message", response.text)
                except:
                    pass
                print(f"Resend: Failed to send email [{response.status_code}]: {error_msg}")
                return False
        except Exception as e:
            print(f"Resend: Exception sending email: {str(e)}")
            return False
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "registration") -> bool:
        """Send OTP via Resend"""
        subject = {
            "registration": "Verify Your Email - CareerLens",
            "login_2fa": "Login Verification Code - CareerLens",
            "password_reset": "Password Reset Code - CareerLens"
        }.get(purpose, "Verification Code - CareerLens")
        
        html = self._get_otp_email_body(otp, purpose)
        text = self._get_otp_email_text(otp, purpose)
        return self._send_email(recipient_email, subject, html, text=text)
    
    def send_newsletter_confirmation(self, subscriber_email: str) -> bool:
        """Send newsletter confirmation via Resend"""
        subject = "Welcome to the CareerLens Newsletter"
        html = self._get_newsletter_email_body()
        text = self._get_newsletter_email_text()
        headers = {
            "List-Unsubscribe": "<mailto:support@careerlens.in?subject=unsubscribe>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }
        return self._send_email(subscriber_email, subject, html, text=text, headers=headers)
    
    def send_contact_email(self, contact_data: Dict[str, str]) -> bool:
        """Send contact form alert to admin inbox via Resend"""
        recipient_email = self.contact_form_email
        name = contact_data.get("name", "")
        sender_email = contact_data.get("email", "")
        subject = contact_data.get("subject", "Contact Form Submission")
        role = contact_data.get("role", "")
        message = contact_data.get("message", "")
        
        email_subject = f"CareerLens Contact: {subject} - From {name}"
        html = self._get_contact_email_body(name, subject)
        text = self._get_contact_email_text(name, sender_email, role, subject, message)
        return self._send_email(recipient_email, email_subject, html, text=text, reply_to=sender_email)

    def _get_otp_email_text(self, otp: str, purpose: str) -> str:
        title = {
            "registration": "Email Verification",
            "login_2fa": "Two-Step Authentication",
            "password_reset": "Password Reset Request"
        }.get(purpose, "Verification Code")
        return (
            f"CareerLens - {title}\n\n"
            f"Your verification code is: {otp}\n"
            "This code expires in 10 minutes.\n"
            "Do not share this code with anyone."
        )

    def _get_newsletter_email_text(self) -> str:
        return (
            "Welcome to the CareerLens Newsletter!\n\n"
            "Thank you for subscribing. You will receive career insights, product updates, "
            "and practical guidance from the CareerLens team.\n\n"
            "To unsubscribe, contact support@careerlens.in"
        )

    def _get_contact_email_text(
        self,
        name: str,
        email: str,
        role: str,
        subject: str,
        message: str,
    ) -> str:
        return (
            "New CareerLens contact form submission\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Role: {role}\n"
            f"Subject: {subject}\n\n"
            "Message:\n"
            f"{message}"
        )
    
    def _get_otp_email_body(self, otp: str, purpose: str) -> str:
        """Generate OTP email HTML body (without CID for Resend)"""
        title = {
            "registration": "Email Verification",
            "login_2fa": "Two-Step Authentication",
            "password_reset": "Password Reset Request"
        }.get(purpose, "Verification Code")
        
        message = {
            "registration": "Welcome to CareerLens! Please verify your email address to complete your registration and start exploring career opportunities.",
            "login_2fa": "A sign-in attempt requires further verification. Enter the code below to securely access your account.",
            "password_reset": "We received a request to reset your CareerLens password. Use the verification code below to securely create a new password."
        }.get(purpose, "Use this code to verify your request.")
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="{self.logo_url}" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        {title}
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        {message}
                      </p>
                      
                      <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0f9ff; border: 1px solid rgba(0, 194, 203, 0.3); border-radius: 12px; margin-bottom: 30px;">
                        <tr>
                          <td align="center" style="padding: 24px;">
                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #00C2CB; display: block;">
                              {otp}
                            </span>
                          </td>
                        </tr>
                      </table>
                      
                      <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-align: center;">
                        This code will securely expire in <strong style="color: #475569;">10 minutes</strong>.
                      </p>
                      
                      <p style="margin: 0; font-size: 14px; color: #ef4444; font-weight: 500; text-align: center;">
                        Please do not share this code with anyone.
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you did not request this email, there is nothing you need to do. Because this is a security notification, you may still receive it even if you have opted out of marketing emails.
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''
    
    def _get_newsletter_email_body(self) -> str:
        """Generate newsletter confirmation email body"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Welcome to CareerLens Newsletter</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="{self.logo_url}" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        Welcome to the CareerLens Newsletter!
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        Thank you for subscribing! You will now receive the latest updates on AI-powered career insights, new platform features, and tips for students and recruiters.
                      </p>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 14px; color: #64748b; text-align: center; line-height: 1.8;">
                        <strong style="color: #0f172a;">What to expect:</strong><br/>
                        🚀 AI-powered career insights and industry trends<br/>
                        ✨ New platform features and improvements<br/>
                        📊 Tips for leveraging data-driven career analysis<br/>
                        💡 Exclusive insights for students and recruiters
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you wish to unsubscribe or manage your preferences, please contact us at support@careerlens.in
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''
    
    def _get_contact_email_body(self, name: str, subject: str) -> str:
        """Generate contact form confirmation email body"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>We Received Your Message</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="{self.logo_url}" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        We Received Your Message
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        Hi {name},<br/>Thank you for reaching out to us! We have received your message regarding <strong>{subject}</strong> and will get back to you as soon as possible.
                      </p>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 14px; color: #64748b; text-align: center;">
                        Our team typically responds within 24-48 business hours. In the meantime, feel free to explore more features on our platform or check our documentation.
                      </p>
                    </td>
                  </tr>
                  
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you have any urgent concerns, please contact us directly at support@careerlens.in
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
                      </p>
                    </td>
                  </tr>
                  
                </table>
                
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''


def get_email_provider() -> EmailProvider:
    """
    Factory function to get the configured email provider
    Supports: smtp (default), resend
    """
    provider_type = os.getenv("EMAIL_PROVIDER", "smtp").lower().strip()
    
    if provider_type == "resend":
        provider = ResendEmailProvider()
        if provider.is_configured():
            print("✓ Using Resend email provider")
            return provider
        else:
            print("⚠ Resend not configured, falling back to SMTP")
            return SMTPEmailProvider()
    else:
        print("✓ Using SMTP email provider")
        return SMTPEmailProvider()


# Global provider instance
_email_provider: Optional[EmailProvider] = None


def init_email_provider() -> EmailProvider:
    """Initialize and return the email provider"""
    global _email_provider
    _email_provider = get_email_provider()
    return _email_provider


def get_current_provider() -> EmailProvider:
    """Get the current email provider instance"""
    global _email_provider
    if _email_provider is None:
        _email_provider = get_email_provider()
    return _email_provider
