from django.db.models.signals import post_save
from django.dispatch import receiver
from students.models import CustomUser

@receiver(post_save, sender=CustomUser)
def update_amount_owed(sender, instance, created, **kwargs):
    # Only run if user has a course
    if instance.course:
        # Avoid recursion by checking if the value actually needs updating
        if instance.amount_owed != instance.course.price:
            CustomUser.objects.filter(pk=instance.pk).update(amount_owed=instance.course.price)
