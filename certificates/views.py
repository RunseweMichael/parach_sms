from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Certificate
from .serializers import CertificateSerializer
from .utils import generate_certificate_image
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.core.files import File
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all().select_related("student", "course")
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        Approve a certificate and generate the certificate image.
        `pk` here is the certificate_id
        """
        try:
            certificate = self.get_object()
        
            # ✅ Check if certificate is obsolete
            if certificate.is_obsolete:
                return Response(
                    {"error": "Cannot approve an obsolete certificate. This certificate is for a course the student no longer takes."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # Check if already approved
            if certificate.is_approved:
                return Response(
                    {"message": "Certificate is already approved."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # Validate required data
            if not certificate.student:
                return Response(
                    {"error": "Certificate has no associated student."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            if not certificate.course:
                return Response(
                    {"error": "Certificate has no associated course."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            course = certificate.course
            logger.info(f"Generating certificate for student: {certificate.student.username}")

            # ✅ Generate certificate image (now includes skills)
            try:
                cert_path = generate_certificate_image(
                    student=certificate.student,
                    course_name=course.course_name,
                    issue_date=certificate.issue_date,
                    certificate_number=certificate.certificate_number,
                    skills=course.skills,
                )

                # ✅ Assign generated file path
                certificate.certificate_file.name = cert_path
                certificate.is_approved = True
                certificate.save()

                # Send Email Notifications
                student = certificate.student
                course = certificate.course
                admin_email = getattr(settings, "ADMIN_EMAIL", None)

                # ✉️ Email to Student (HTML)
                try:
                    from django.template.loader import render_to_string
                    from django.utils import timezone
                    
                    context = {
                        "name": student.name or student.email,
                        "course_name": course.course_name,
                        "year": timezone.now().year,
                        "dashboard_url": "https://yourdomain.com/dashboard",
                        "logo": "https://parachictacademy.com.ng/wp-content/uploads/2019/08/Parach-computers-ibadan-logo-1-e1565984209812.png"
                    }

                    html_message = render_to_string("emails/certificate_student.html", context)

                    send_mail(
                        subject="🎉 Congratulations! Your Certificate Has Been Approved",
                        message="Your email client does not support HTML.",
                        html_message=html_message,
                        from_email=f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>",
                        recipient_list=[student.email],
                        fail_silently=True,
                    )

                except Exception as e:
                    logger.error(f"Failed to send student certificate email: {e}")

                # ✉️ Email to Admin (HTML)
                if admin_email:
                    try:
                        from django.template.loader import render_to_string
                        
                        admin_context = {
                            "name": student.name,
                            "email": student.email,
                            "course_name": course.course_name,
                            "certificate_no": certificate.certificate_number,
                        }

                        admin_html = render_to_string("emails/certificate_admin.html", admin_context)

                        send_mail(
                            subject="📢 Student Course Completed & Certificate Approved",
                            message="Your email client does not support HTML.",
                            html_message=admin_html,
                            from_email=f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>",
                            recipient_list=[admin_email],
                            fail_silently=True,
                        )

                    except Exception as e:
                        logger.error(f"Failed to send admin certificate approval email: {e}")

            except Exception as img_error:
                logger.error(f"Certificate image generation failed: {str(img_error)}")
                return Response(
                    {"error": f"Failed to generate certificate image: {str(img_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"Certificate {certificate.certificate_number} approved successfully")

            # ✅ Return updated certificate data
            serializer = self.get_serializer(certificate)
            return Response(
                {
                    "message": "Certificate approved and generated successfully!",
                    "certificate": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Certificate.DoesNotExist:
            return Response(
                {"error": "Certificate not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Approval failed: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to approve certificate: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        """
        Filter certificates based on user role and query params.
        By default, hide obsolete certificates unless explicitly requested.
        """
        queryset = Certificate.objects.all()

        # Filter by student if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(student=self.request.user)

        # ✅ Filter obsolete certificates (default: hide them)
        show_obsolete = self.request.query_params.get("show_obsolete", "true")
        if show_obsolete.lower() not in ["true", "1"]:
            queryset = queryset.filter(is_obsolete=False)

        # Apply is_approved query param filter
        is_approved = self.request.query_params.get("is_approved")
        if is_approved is not None:
            if is_approved.lower() in ["true", "1"]:
                queryset = queryset.filter(is_approved=True)
            elif is_approved.lower() in ["false", "0"]:
                queryset = queryset.filter(is_approved=False)

        return queryset
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """
        Get all certificates pending approval (excluding obsolete ones).
        Admin-only endpoint.
        """
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_certs = Certificate.objects.filter(
            is_approved=False,
            is_obsolete=False
        ).select_related('student', 'course')
        
        serializer = self.get_serializer(pending_certs, many=True)
        return Response(serializer.data)