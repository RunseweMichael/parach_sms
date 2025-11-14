from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from students.models import CustomUser
from certificates.models import Certificate
from .models import Notification, AdminActivity
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def notify_new_student(sender, instance, created, **kwargs):
    """Create notification when new student registers"""
    if created and not instance.is_staff:
        try:
            Notification.objects.create(
                title="New Student Registration",
                message=f"New student {instance.username} has registered for {instance.course.course_name if instance.course else 'a course'}",
                priority="MEDIUM"
            )
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")


@receiver(post_save, sender=Certificate)
def notify_certificate_created(sender, instance, created, **kwargs):
    """Create notification when certificate is created"""
    if created:
        try:
            Notification.objects.create(
                title="New Certificate Created",
                message=f"Certificate created for {instance.student.username} - {instance.certificate_number}",
                priority="MEDIUM"
            )
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")


@receiver(post_save, sender=Certificate)
def notify_certificate_approved(sender, instance, created, **kwargs):
    """Create notification when certificate is approved"""
    if not created and instance.is_approved:
        try:
            # Check if notification already exists
            existing = Notification.objects.filter(
                title="Certificate Approved",
                message__contains=instance.certificate_number
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    title="Certificate Approved",
                    message=f"Certificate {instance.certificate_number} has been approved for {instance.student.username}",
                    priority="HIGH"
                )
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log admin login"""
    if user.is_staff:
        try:
            ip_address = request.META.get('REMOTE_ADDR')
            AdminActivity.objects.create(
                admin=user,
                action='LOGIN',
                model_name='User',
                description=f"Admin {user.username} logged in",
                ip_address=ip_address
            )
        except Exception as e:
            logger.error(f"Failed to log login: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log admin logout"""
    if user and user.is_staff:
        try:
            ip_address = request.META.get('REMOTE_ADDR')
            AdminActivity.objects.create(
                admin=user,
                action='LOGOUT',
                model_name='User',
                description=f"Admin {user.username} logged out",
                ip_address=ip_address
            )
        except Exception as e:
            logger.error(f"Failed to log logout: {str(e)}")