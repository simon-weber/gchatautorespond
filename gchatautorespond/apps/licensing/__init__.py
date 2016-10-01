from django.dispatch import receiver
from registration.signals import user_activated

from .lib import save_init_license


@receiver(user_activated)
def handle_activate(sender, user, **kwargs):
    save_init_license(user)
