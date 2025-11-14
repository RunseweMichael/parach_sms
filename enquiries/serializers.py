from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from .models import Enquiry


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate_consent(self, value):
        """Ensure the user has given consent before submitting the enquiry."""
        if not value:
            raise serializers.ValidationError("Consent must be given to submit an enquiry.")
        return value

    def validate_phone(self, value):
        """Basic validation for phone number format (optional)."""
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits long.")
        return value

    def create(self, validated_data):
        """Send email notifications when a new enquiry is created."""
        enquiry = Enquiry.objects.create(**validated_data)

        from_email = f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>"

        # --- 1️⃣ Notify Admin (Styled HTML) ---
        admin_subject = f"📩 New Enquiry from {enquiry.name}"

        admin_plain_message = (
            f"New enquiry received:\n\n"
            f"Name: {enquiry.name}\n"
            f"Email: {enquiry.email}\n"
            f"Phone: {enquiry.phone}\n"
            f"Gender: {enquiry.gender}\n"
            f"Course: {enquiry.course}\n"
            f"Message: {enquiry.message}\n\n"
            f"Please log in to the admin panel to manage this enquiry."
        )

        admin_html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                
                <h2 style="color: #0066cc;">📩 New Enquiry Received</h2>
                <p><strong>Name:</strong> {enquiry.name}</p>
                <p><strong>Email:</strong> {enquiry.email}</p>
                <p><strong>Phone:</strong> {enquiry.phone}</p>
                <p><strong>Gender:</strong> {enquiry.gender}</p>
                <p><strong>Course:</strong> {enquiry.course}</p>
                <p><strong>Message:</strong></p>
                <blockquote style="background:#f8f9fa; padding:10px; border-left:3px solid #0066cc; color:#333;">
                    {enquiry.message}
                </blockquote>
                <p style="margin-top:20px;">
                    <a href="https://your-admin-url.com" style="background:#0066cc; color:white; 
                    padding:10px 15px; text-decoration:none; border-radius:5px;">Open Admin Panel</a>
                </p>
                <hr>
                <p style="font-size:13px; color:#555;">
                    <strong>Sent from Parach Academy Enquiry System</strong><br>
                    <a href="mailto:{settings.DEFAULT_FROM_EMAIL}" style="color:#0066cc;">{settings.DEFAULT_FROM_EMAIL}</a>
                </p>
            </div>
        </body>
        </html>
        """

        try:
            send_mail(
                admin_subject,
                admin_plain_message,
                from_email,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
                html_message=admin_html_message
            )
        except Exception as e:
            print("Admin email failed:", e)
            

        # --- 2️⃣ HTML Auto-Reply to User ---
        user_subject = f"Thanks for contacting us, {enquiry.name}!"
        plain_message = (
            f"Hi {enquiry.name},\n\n"
            f"Thank you for enquiring about our {enquiry.course} course.\n"
            f"Our team will reach out soon.\n\n"
            f"Best regards,\n"
            f"The Parach Team"
        )

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color:#f8f9fa; padding:20px;">
            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color:#0066cc;">Thank you for your enquiry, {enquiry.name}!</h2>
                <p>
                    We’ve received your enquiry about the <strong>{enquiry.course}</strong> course.
                    One of our team members will contact you soon with more details.
                </p>
                <p style="background:#f1f1f1; padding:10px; border-radius:5px;">
                    <strong>Your Message:</strong><br>
                    {enquiry.message}
                <p>
                    If you have any urgent inquiries, please do not hesitate to reply to this email or contact us via phone at 
                    <a href="tel:+2347055247562">+234 705 524 7562</a> or via WhatsApp: 
                    <a href="https://wa.me/message/UJKCEH4WSDYFL1" target="_blank" rel="noopener">Chat with us on WhatsApp</a>.
                </p>
                <p>
                    You can also download our Price List here: 
                    <a href="https://parachictacademy.com.ng/wp-content/uploads/2025/07/Tech-schools-in-Ibadan_Parach-Course-List.pdf" target="_blank" rel="noopener">Download Our Price List</a>.
                </p>
                <hr>
                <p style="font-size:13px; color:#555;">
                    Best regards,<br>
                    <strong>The Parach Team</strong><br>
                    <a href="mailto:{settings.DEFAULT_FROM_EMAIL}">{settings.DEFAULT_FROM_EMAIL}</a>
                </p>
            </div>
        </body>
        </html>
        """

        try:
            send_mail(
                user_subject,
                plain_message,
                from_email,
                [enquiry.email],
                fail_silently=True,
                html_message=html_message
            )
        except Exception as e:
            print("Auto-reply email failed:", e)

        return enquiry
