from django.db import models
from courses.models import Courses

class Enquiry(models.Model):
    ENQUIRY_STATUS = [
        ('NEW', 'New'),
        ('FOLLOWED_UP', 'Followed Up'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    CENTER_CHOICES = [
        ("Orogun", "Orogun"),
        ("Samonda", "Samonda"),
        ("Online", "Online"),
    ]
    
    name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(blank=False, null=False)
    phone = models.CharField(max_length=15, blank=False, null=False)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    center = models.CharField(max_length=20, choices=CENTER_CHOICES, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENQUIRY_STATUS, default='NEW')
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True, blank=True)
    consent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.name} - {self.course.course_name if self.course else 'General Enquiry'}"

