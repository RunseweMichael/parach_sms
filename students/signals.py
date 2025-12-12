from django.db.models.signals import post_save
from django.dispatch import receiver
from students.models import CustomUser

@receiver(post_save, sender=CustomUser)
def update_amount_owed(sender, instance, created, **kwargs):
    if instance.course:
        # Update without triggering recursion
        if instance.amount_owed != instance.course.price:
            CustomUser.objects.filter(pk=instance.pk).update(amount_owed=instance.course.price)








# This is for the onboarding. When a student completes his/her registration and made first payment.
# This would trigger a signal and send an email to the student as well as the admin for record keeping.
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import CustomUser

@receiver(pre_save, sender=CustomUser)
def send_onboarding_after_first_payment(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = CustomUser.objects.get(pk=instance.pk)
    except CustomUser.DoesNotExist:
        return

    # FIRST PAYMENT DETECTED
    if old.amount_paid == 0 and instance.amount_paid > 0:

        # ======================================
        #  STUDENT EMAIL (HTML)
        # ======================================
        context = {
            "name": instance.name or instance.email,
            "year": timezone.now().year,
            "logo": "https://parachictacademy.com.ng/wp-content/uploads/2019/08/Parach-computers-ibadan-logo-1-e1565984209812.png",  # ADD YOUR LOGO URL
            "dashboard_url": "https://parach-sms.vercel.app/student/dashboard",       # UPDATE WITH ACTUAL DASHBOARD URL
        }
        

        html_message = render_to_string("emails/onboarding_student.html", context)

        send_mail(
            subject="Welcome! Your Registration Payment Was Received",
            message="Your email client does not support HTML.",
            html_message=html_message,
            from_email= f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>",
            recipient_list=[instance.email],
            fail_silently=True,
        )

        # ======================================
        #  ADMIN EMAIL (HTML)
        # ======================================
        admin_email = getattr(settings, "ADMIN_EMAIL", None)
        if admin_email:
            admin_context = {
                "name": instance.name,
                "email": instance.email,
                "amount": instance.amount_paid,
            }
            admin_html = render_to_string("emails/onboarding_admin.html", admin_context)

            send_mail(
                subject="New Student Payment Received",
                message="HTML email not supported.",
                html_message=admin_html,
                from_email= f"Parach ICT Academy <{settings.DEFAULT_FROM_EMAIL}>",
                recipient_list=[admin_email],
                fail_silently=True,
            )
