from django.db.models.signals import post_save
from django.dispatch import receiver
from students.models import CustomUser

@receiver(post_save, sender=CustomUser)
def update_amount_owed(sender, instance, created, **kwargs):
    if instance.course:
        # Update without triggering recursion
        if instance.amount_owed != instance.course.price:
            CustomUser.objects.filter(pk=instance.pk).update(amount_owed=instance.course.price)
