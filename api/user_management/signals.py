
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from social_media.models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, *args, **kwargs):
    if created:
        Profile.objects.create(user=instance)
