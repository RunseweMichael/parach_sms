from django.db import models
from django.conf import settings

class InternshipRequest(models.Model):
    DURATION_CHOICES = [
        ("3 months", "3 months"),
        ("6 months", "6 months"),
        ("9 months", "9 months"),
        ("1 year", "1 year"),
    ]

    student_name = models.CharField(max_length=255)
    student_email = models.EmailField()
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    preferred_start_date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    # admin fields
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    internship_pdf = models.FileField(upload_to="internship_letters/", null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student_name} — {self.duration} — {self.student_email}"
