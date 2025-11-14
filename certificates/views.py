from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Certificate
from .serializers import CertificateSerializer
from .utils import generate_certificate_image
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.core.files import File
import logging

logger = logging.getLogger(__name__)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all().select_related("student", "course")
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]  # Changed from IsAdminUser for testing

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        Approve a certificate and generate the certificate image.
        `pk` here is the certificate_id
        """
        try:
            certificate = self.get_object()
        
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
        queryset = Certificate.objects.all()  # start with all certificates

        # Only filter by student if request is coming from the API (not admin)
        if self.request.user.is_staff is False:
            queryset = queryset.filter(student=self.request.user)

        # Apply is_approved query param filter
        is_approved = self.request.query_params.get("is_approved")
        if is_approved is not None:
            if is_approved.lower() in ["true", "1"]:
                queryset = queryset.filter(is_approved=True)
            elif is_approved.lower() in ["false", "0"]:
                queryset = queryset.filter(is_approved=False)

        return queryset

