from bee.signals import user_signed_up
from django.dispatch import receiver
from .models import Role, User

@receiver(user_signed_up)
def assign_user_role(sender, request, user, **kwargs):
    default_role, _ = Role.objects.get_or_create(name='user')
    user.role = default_role
    user.full_name = user.get_full_name() or user.username
    user.save()
