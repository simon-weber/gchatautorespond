import datetime

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from gchatautorespond.apps.licensing.models import CurrentLicense


class Command(BaseCommand):
    help = 'Prints user emails to stdout for import into eg mailchimp.'

    def handle(self, *args, **options):
        # Licensed users, and anyone active in the past 6 months,

        cutoff = datetime.datetime.now() - datetime.timedelta(days=30 * 6)
        actives = User.objects.filter(
            Q(is_active=True) & (
                Q(date_joined__gt=cutoff) | Q(last_login__gt=cutoff)
            )
        )
        emails = {user.email for user in actives}

        for currentlicense in CurrentLicense.objects.all():
            if currentlicense.license.is_active:
                emails.add(currentlicense.license.user.email)

        for email in emails:
            print email
