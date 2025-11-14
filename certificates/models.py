from django.db import models
from django.utils import timezone
from django.conf import settings
from students.models import CustomUser
from courses.models import Courses
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class Certificate(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("courses.Courses", on_delete=models.SET_NULL, null=True, blank=True)
    issue_date = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)
    certificate_file = models.FileField(upload_to="certificates/", blank=True, null=True)
    certificate_number = models.CharField(max_length=50, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = f"CERT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        student_name = getattr(self.student, "name", None) or getattr(self.student, "username", "Unknown Student")
        course_name = getattr(self.course, "course_name", "No Course")
        return f"{student_name} - {course_name}"
