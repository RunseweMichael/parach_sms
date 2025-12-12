# users/models.py
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from decimal import Decimal
import random
import hashlib
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)


class CustomUserManager(BaseUserManager):
    """Custom manager where email is the unique identifier for authentication"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    CENTER_CHOICES = [
        ("Orogun", "Orogun"),
        ("Samonda", "Samonda"),
        ("Online", "Online"),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    center = models.CharField(max_length=20, choices=CENTER_CHOICES, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    course = models.ForeignKey('courses.Courses', on_delete=models.SET_NULL, null=True, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    consent = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    next_due_date = models.DateField(blank=True, null=True)
    dashboard_locked = models.BooleanField(default=False)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    has_used_coupon = models.BooleanField(default=False)

    # Required permission fields
    is_active = models.BooleanField(default=True)
    # role fields
    is_superadmin = models.BooleanField(default=False)
    is_staff_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        if self.amount_owed > 0 and not self.next_due_date:
            self.next_due_date = timezone.now().date() + timedelta(days=30)

        if self.course:
            min_required = self.course.price * Decimal('0.5')
            if self.next_due_date and timezone.now().date() > self.next_due_date and self.amount_paid < min_required:
                self.dashboard_locked = True
            else:
                self.dashboard_locked = False

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or str(self.id)


# -------------------------------
# EMAIL OTP MODEL
# -------------------------------
class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)  # Store hashed if you want extra security
    purpose = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = 5

    def __str__(self):
        return f"{self.user.email} – {self.code}"

    @classmethod
    def generate_otp(cls, user, purpose=None):
        """Generate a unique OTP per user and purpose"""
        code = f"{random.randint(100000, 999999)}"
        while cls.objects.filter(user=user, code=code, is_used=False, purpose=purpose).exists():
            code = f"{random.randint(100000, 999999)}"

        # Optional: hash code for security
        # hashed_code = hashlib.sha256(code.encode()).hexdigest()

        expires_at = timezone.now() + timedelta(minutes=5)
        otp = cls.objects.create(user=user, code=code, purpose=purpose, expires_at=expires_at)
        return otp

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def increment_attempt(self):
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.mark_as_used()
        self.save(update_fields=['attempts', 'is_used'])

    @classmethod
    def clean_expired_otps(cls):
        cls.objects.filter(expires_at__lt=timezone.now(), is_used=False).delete()


# -------------------------------
# DRF TOKEN SIGNAL
# -------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
