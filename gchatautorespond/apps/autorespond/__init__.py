from django.dispatch import receiver
from registration.signals import user_activated, user_registered

from gchatautorespond.lib import report_ga_event_async


@receiver(user_activated)
def handle_activate(sender, user, **kwargs):
    report_ga_event_async(user.email, category='user', action='activate')


@receiver(user_registered)
def handle_register(sender, user, **kwargs):
    report_ga_event_async(user.email, category='user', action='register')
