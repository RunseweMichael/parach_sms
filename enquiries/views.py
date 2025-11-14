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
        from_email = "Parach ICT Academy <runsewemichael93@gmail.com>"  # Replace with your sender email
        to_email = [enquiry.email]

        # Plain text content (fallback)
        text_content = f"""
Hi {enquiry.name},

Thank you for visiting us and showing interest in our courses.

We’d like to follow up to ensure you have all the information you need to get started.

If you have any questions or need guidance on course selection, please don’t hesitate to reach out.

Best regards,
Your Organization Team
        """

        # HTML content
        html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height:1.6; color:#333;">
    <div style="max-width:600px; margin:auto; padding:20px; border:1px solid #e2e8f0; border-radius:10px;">
      <h2 style="color:#1e3a8a;">Hello {enquiry.name},</h2>
      <p>Thank you for visiting Parach ICT Academy and showing interest in our courses.</p>
      <p>We wanted to follow up to ensure you have all the information you need to get started.</p>
      <p>If you have any questions or need guidance on course selection, feel free to <a href="mailto:runsewemichael93@gmail.com" style="color:#3b82f6;">contact us</a>.</p>
      <br>
        <p>
            If you have any urgent inquiries, please do not hesitate to reply to this email or contact us via phone at 
            <a href="tel:+2347055247562">+234 705 524 7562</a> or via WhatsApp: 
            <a href="https://wa.me/message/UJKCEH4WSDYFL1" target="_blank" rel="noopener">Chat with us on WhatsApp</a>.
        </p>
      <p style="margin-top:20px;">Best regards,<br>
      <strong>Parach ICT Academy</strong></p>
    </div>
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
