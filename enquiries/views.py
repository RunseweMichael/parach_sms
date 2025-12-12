from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import requests
from .models import Enquiry
from .serializers import EnquirySerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all().order_by('-created_at')
    serializer_class = EnquirySerializer
    permission_classes = [AllowAny]

    def normalize_phone(self, number):
        """Convert phone number to international format (Nigeria example)."""
        if not number:
            return None
        number = number.strip().replace(" ", "")
        if number.startswith("0"):
            number = "234" + number[1:]
        elif number.startswith("+"):
            number = number[1:]
        return number  # Return without '+' prefix for Termii

    def send_sms_via_termii(self, phone, message):
        """Send SMS using Termii API."""
        termii_api_key = getattr(settings, 'TERMII_API_KEY', None)
        termii_base_url = getattr(settings, 'TERMII_BASE_URL', 'https://api.ng.termii.com')
        
        if not termii_api_key:
            return False, "Termii API key not configured"

        normalized_phone = self.normalize_phone(phone)
        if not normalized_phone:
            return False, "Invalid phone number"

        payload = {
            "to": normalized_phone,
            "from": "ParachICT",
            "sms": message,
            "type": "plain",
            "channel": "generic",
            "api_key": termii_api_key
        }

        try:
            response = requests.post(
                f"{termii_base_url}/api/sms/send",
                json=payload,
                timeout=10
            )
            response_data = response.json()
            
            if response.status_code == 200:
                return True, response_data
            else:
                return False, response_data
        except Exception as e:
            return False, str(e)

    def send_enquiry_followup_email(self, enquiry):
        """Send follow-up email to enquiry with consistent Parach branding."""
        subject = "Thank You for Your Interest in Our Courses!"
        from_email = "Parach ICT Academy <parachcomputers@gmail.com>"
        to_email = [enquiry.email]

        # Plain text content (fallback)
        text_content = f"""
Hi {enquiry.name},

Thank you for visiting Parach ICT Academy and showing interest in our courses.

We'd like to follow up to ensure you have all the information you need to get started.

You can view all our courses here: https://parachictacademy.com.ng

If you have any questions or need guidance on course selection, please don't hesitate to reach out.

Best regards,
Parach ICT Academy
"""

        # HTML content with Parach branding (matching onboarding email style)
        course_name = enquiry.course.course_name if enquiry.course else "our courses"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en" style="margin:0; padding:0;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Your Interest</title>
</head>

<body style="font-family:Arial, sans-serif; background:#f5f7fa; padding:0; margin:0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" 
                       style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                    
                    <!-- Header with Logo -->
                    <tr>
                        <td style="background:#1e293b; padding:30px 20px; text-align:center;">
                            <img src="https://parachictacademy.com.ng/wp-content/uploads/2019/08/Parach-computers-ibadan-logo-1-e1565984209812.png" 
                                 alt="Parach ICT Academy" 
                                 style="max-width:180px; height:auto; margin-bottom:15px;">
                            <h2 style="color:white; margin:0; font-size:22px;">Thank You for Your Interest!</h2>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding:30px;">
                            <p style="font-size:15px; color:#444;">Hello {enquiry.name},</p>

                            <p style="font-size:15px; color:#555; line-height:1.6;">
                                Thank you for visiting <strong>Parach ICT Academy</strong> and expressing interest in <strong>{course_name}</strong>.
                            </p>

                            <p style="font-size:15px; color:#555; line-height:1.6;">
                                We wanted to follow up to ensure you have all the information you need to get started on your journey to tech excellence.
                            </p>

                            <!-- Call to Action Button -->
                            <div style="text-align:center; margin:30px 0;">
                                <a href="https://parachictacademy.com.ng/wp-content/uploads/2025/07/Tech-schools-in-Ibadan_Parach-Course-List.pdf" 
                                   style="background:#3b82f6; color:white; text-decoration:none; padding:14px 28px; 
                                          border-radius:6px; display:inline-block; font-weight:bold; font-size:15px;">
                                   📄 View Course List & Pricing
                                </a>
                            </div>

                            <!-- Contact Information Box -->
                            <div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:15px; margin:20px 0; border-radius:4px;">
                                <p style="margin:0 0 10px 0; font-size:15px; color:#333; font-weight:bold;">
                                    📞 Need More Information?
                                </p>
                                <ul style="font-size:14px; color:#555; line-height:1.8; margin:0; padding-left:20px;">
                                    <li>Call us: <a href="tel:+2347055247562" style="color:#3b82f6; text-decoration:none;">+234 705 524 7562</a></li>
                                    <li>WhatsApp: <a href="https://wa.me/message/UJKCEH4WSDYFL1" style="color:#3b82f6; text-decoration:none;" target="_blank">Chat with us</a></li>
                                    <li>Email: <a href="mailto:parachcomputers@gmail.com" style="color:#3b82f6; text-decoration:none;">parachcomputers@gmail.com</a></li>
                                    <li>Website: <a href="https://parachictacademy.com.ng" style="color:#3b82f6; text-decoration:none;" target="_blank">parachictacademy.com.ng</a></li>
                                </ul>
                            </div>

                            <p style="font-size:15px; color:#555; line-height:1.6;">
                                Our team is ready to help you choose the right course and answer any questions you may have.
                            </p>

                            <p style="font-size:15px; color:#555; margin-top:25px;">
                                Best regards,<br>
                                <strong>The Parach ICT Academy Team</strong>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background:#f0f3f8; padding:20px; text-align:center;">
                            <p style="margin:0; font-size:13px; color:#7a7a7a;">
                                Parach ICT Academy — Follow-Up Email
                            </p>
                            <p style="margin:5px 0 0 0; font-size:12px; color:#999;">
                                Building Tech Skills for Tomorrow
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        # Send email
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @action(detail=True, methods=['POST'])
    def send_email(self, request, pk=None):
        """Send follow-up email and SMS to enquiry."""
        enquiry = self.get_object()
        email_success = False
        sms_success = False
        email_error = None
        sms_error = None

        # Send Email
        try:
            self.send_enquiry_followup_email(enquiry)
            email_success = True
        except Exception as e:
            email_error = str(e)

        # Send SMS
        course_name = enquiry.course.course_name if enquiry.course else "our courses"
        sms_message = (
            f"Dear {enquiry.name}, thank you for expressing interest in {course_name} at Parach ICT Academy. "
            f" Visit https://parachictacademy.com.ng/ or call us at +234 705 524 7562."
        )
        
        sms_success, sms_response = self.send_sms_via_termii(enquiry.phone, sms_message)
        if not sms_success:
            sms_error = sms_response

        # Prepare response
        response_data = {
            'email': {
                'success': email_success,
                'error': email_error
            },
            'sms': {
                'success': sms_success,
                'error': sms_error if not sms_success else None,
                'response': sms_response if sms_success else None
            }
        }

        # Determine overall status
        if email_success and sms_success:
            response_data['status'] = 'Email and SMS sent successfully'
            return Response(response_data)
        elif email_success or sms_success:
            response_data['status'] = 'Partially sent'
            return Response(response_data, status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            response_data['status'] = 'Failed to send'
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)