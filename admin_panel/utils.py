from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)


def create_notification(title, message, priority='MEDIUM', user=None):
    """Helper function to create notifications"""
    try:
        notification = Notification.objects.create(
            title=title,
            message=message,
            priority=priority,
            created_for=user
        )
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None


def send_email_notification(subject, message, recipient_list):
    """Send email notification"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def generate_report(report_type, start_date=None, end_date=None):
    """Generate various types of reports"""
    from students.models import CustomUser
    from certificates.models import Certificate
    from django.db.models import Sum, Count, Q
    
    report_data = {}
    
    try:
        if report_type == 'financial':
            students = CustomUser.objects.filter(is_staff=False)
            if start_date:
                students = students.filter(registration_date__gte=start_date)
            if end_date:
                students = students.filter(registration_date__lte=end_date)
            
            report_data = students.aggregate(
                total_revenue=Sum('amount_paid'),
                total_outstanding=Sum('amount_owed'),
                total_students=Count('id')
            )
        
        elif report_type == 'certificates':
            certificates = Certificate.objects.all()
            if start_date:
                certificates = certificates.filter(issue_date__gte=start_date)
            if end_date:
                certificates = certificates.filter(issue_date__lte=end_date)
            
            report_data = {
                'total_certificates': certificates.count(),
                'approved': certificates.filter(is_approved=True).count(),
                'pending': certificates.filter(is_approved=False).count(),
            }
        
        elif report_type == 'students':
            students = CustomUser.objects.filter(is_staff=False)
            if start_date:
                students = students.filter(registration_date__gte=start_date)
            if end_date:
                students = students.filter(registration_date__lte=end_date)
            
            report_data = {
                'total_students': students.count(),
                'active_students': students.filter(is_active=True).count(),
                'inactive_students': students.filter(is_active=False).count(),
                'with_consent': students.filter(consent=True).count(),
                'without_consent': students.filter(consent=False).count(),
            }
        
        return report_data
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        return {}


def bulk_send_emails(subject, message, recipient_type='all'):
    """Send bulk emails to students"""
    from students.models import CustomUser
    
    try:
        students = CustomUser.objects.filter(is_staff=False)
        
        if recipient_type == 'active':
            students = students.filter(is_active=True)
        elif recipient_type == 'inactive':
            students = students.filter(is_active=False)
        elif recipient_type == 'defaulters':
            students = students.filter(amount_owed__gt=0)
        
        recipient_list = list(students.values_list('email', flat=True))
        
        if recipient_list:
            return send_email_notification(subject, message, recipient_list)
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to send bulk emails: {str(e)}")