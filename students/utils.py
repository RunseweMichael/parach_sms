# utils.py
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_otp_email(user, otp):
    subject = "Your OTP Verification Code"
    from_email = f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>"
    to = [user.email]

    # Plain text (for email clients that don’t support HTML)
    text_content = f"""
    Hello {user.username or user.email},

    Your verification code is: {otp.code}

    This code will expire in 10 minutes.

    If you didn’t request this, please ignore this email.
    """

    # HTML version (styled)
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9fafb; padding: 30px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
          <h2 style="color: #4a4a4a; text-align: center;">Account Verification</h2>
          <p style="font-size: 16px; color: #333333;">
            Hello <strong>{user.name or user.email}</strong>,
          </p>
          <p style="font-size: 15px; color: #555;">
            Thank you for using our service! Please use the verification code below to complete your process.
          </p>

          <div style="text-align: center; margin: 30px 0;">
            <span style="display: inline-block; font-size: 28px; letter-spacing: 6px; font-weight: bold; color: #2b6cb0;">
              {otp.code}
            </span>
          </div>

          <p style="font-size: 15px; color: #555;">
            This code will expire in <strong>10 minutes</strong>.
          </p>

          <p style="font-size: 14px; color: #777;">
            If you didn’t request this, please ignore this email.
          </p>

          <hr style="margin-top: 30px; border: none; border-top: 1px solid #e0e0e0;">
          <p style="text-align: center; font-size: 12px; color: #aaa;">
            &copy; {user._meta.app_label.title()} | Parach ICT Academy Team
          </p>
        </div>
      </body>
    </html>
    """

    # Send both plain text and HTML versions
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
