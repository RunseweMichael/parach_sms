from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.core.files.base import ContentFile
from admin_panel.permissions import IsSuperAdmin, IsStaffOrSuperAdmin
from rest_framework.decorators import api_view
from django.core.mail import EmailMessage
from django.conf import settings
from .models import InternshipRequest
from .utils import generate_internship_pdf
from .serializers import InternshipRequestSerializer


class InternshipRequestViewSet(viewsets.ModelViewSet):
    queryset = InternshipRequest.objects.all()
    serializer_class = InternshipRequestSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
    
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]

        if self.action == "approve":
            return [IsAuthenticated(), IsStaffOrSuperAdmin()]


        return [IsAuthenticated()]

        

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        internship = self.get_object()
        if internship.is_approved:
            return Response({"detail": "Already approved."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark as approved
        internship.is_approved = True
        internship.approved_at = timezone.now()
        internship.approved_by = request.user
        internship.save()

        # ----------------------------
        # Generate PDF
        # ----------------------------
        pdf_bytes = generate_internship_pdf(internship)

        # Create a filesystem-safe PDF name using the student's name
        import re
        safe_name = re.sub(r'[^A-Za-z0-9_-]', '', internship.student_name.replace(' ', '_'))
        pdf_name = f"{safe_name}_internship_letter.pdf"

        internship.internship_pdf.save(pdf_name, ContentFile(pdf_bytes))
        internship.save()

        # ----------------------------
        # Send Email with PDF
        # ----------------------------
        email = EmailMessage(
            subject="Official Internship Acceptance Letter - Parach ICT Academy",
            body=(
                f"Dear {internship.student_name},\n\n"
                "We are pleased to notify you that your internship application has been successfully approved.\n\n"
                "Kindly review the attached internship offer letter for full details regarding your placement.\n\n"
                "Best regards,\n"
                "Parach ICT Academy Team"
            ),
            from_email=f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>",
            to=[internship.student_email],
            cc=[f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>"],
        )
        email.attach(pdf_name, pdf_bytes, "application/pdf")
        email.send()

        serializer = self.get_serializer(internship)
        return Response(serializer.data, status=status.HTTP_200_OK)



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        print("VALIDATION ERRORS:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        return super().create(request, *args, **kwargs)


