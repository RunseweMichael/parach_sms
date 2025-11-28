from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.core.mail import EmailMultiAlternatives
from .models import Enquiry
from .serializers import EnquirySerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all().order_by('-created_at')
    serializer_class = EnquirySerializer
    permission_classes = [AllowAny]

    def send_enquiry_followup_email(self, enquiry):
      subject = "Thank You for Your Interest in Our Courses!"
      from_email = "Parach ICT Academy <runsewemichael93@gmail.com>"
      to_email = [enquiry.email]

      # Plain text content (fallback)
      text_content = f"""
  Hi {enquiry.name},

  Thank you for visiting Parach ICT Academy and showing interest in our courses.

  We’d like to follow up to ensure you have all the information you need to get started.

  You can view all our courses here: https://parachictacademy.com.ng/courses

  If you have any questions or need guidance on course selection, please don’t hesitate to reach out.

  Best regards,
  Parach ICT Academy
  """

      # HTML content with improved styling
      html_content = f"""
  <html>
    <body style="font-family: Arial, sans-serif; background:#f5f7fa; margin:0; padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" 
                   style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.1);">

              <!-- Header -->
              <tr>
                <td style="background:#1e3a8a; padding:20px; text-align:center;">
                  <h2 style="color:white; margin:0; font-size:22px;">Hello {enquiry.name},</h2>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:30px; color:#333; font-size:15px; line-height:1.6;">
                  <p>Thank you for visiting <strong>Parach ICT Academy</strong> and showing interest in our courses.</p>
                  <p>We wanted to follow up to ensure you have all the information you need to get started.</p>
                  <p>If you have any questions or need guidance on course selection, feel free to 
                     <a href="mailto:runsewemichael93@gmail.com" style="color:#3b82f6; text-decoration:none;">contact us</a>.
                  </p>

                  <!-- Button -->
                  <p style="text-align:center; margin:30px 0;">
                    <a href="https://parachictacademy.com.ng/wp-content/uploads/2025/07/Tech-schools-in-Ibadan_Parach-Course-List.pdf" 
                       style="background:#3b82f6; color:white; text-decoration:none; padding:12px 24px; border-radius:6px; display:inline-block; font-weight:bold;">
                       View Courses
                    </a>
                  </p>

                  <p>
                    For urgent inquiries, you can also call 
                    <a href="tel:+2347055247562" style="color:#3b82f6; text-decoration:none;">+234 705 524 7562</a> 
                    or WhatsApp us 
                    <a href="https://wa.me/message/UJKCEH4WSDYFL1" style="color:#3b82f6; text-decoration:none;" target="_blank" rel="noopener">here</a>.
                  </p>

                  <p style="margin-top:20px;">Best regards,<br>
                  <strong>Parach ICT Academy</strong></p>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background:#f0f3f8; padding:20px; text-align:center; font-size:13px; color:#7a7a7a;">
                  Parach ICT Academy — Follow-Up Email
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
        enquiry = self.get_object()
        try:
            self.send_enquiry_followup_email(enquiry)
            return Response({'status': 'Email sent'})
        except Exception as e:
            return Response({'status': 'Failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
