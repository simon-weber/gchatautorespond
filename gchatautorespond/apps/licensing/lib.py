import logging

import braintree
from django.conf import settings
from django.core import serializers
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
import requests

from gchatautorespond.lib import report_ga_event_async
from .models import License, CurrentLicense

logger = logging.getLogger(__name__)


def report_bt_event(email, result, object, action):
    value = 1 if result.is_success else -1
    report_ga_event_async(email, category=object, action=action, label='braintree', value=value)


def _transition_autoresponses(action, user):
    for autorespond in user.autoresponse_set.all():
        requests.post("http://127.0.0.1:%s/%s/%s" % (settings.WORKER_PORT, action, autorespond.id))


def notify_of_trial_expiry(user):
    paragraphs = [
        'Hi there!',
        'Your trial at https://gchat.simon.codes has just expired and your autoresponses have been disabled.',
        'To enable them again, buy a subscription at https://gchat.simon.codes/payment/detail.',
        "It's only %s per month -- less than a cup of coffee!" % settings.PRICE_REPR,
    ]
    email = EmailMessage(
        subject='trial expired, autoresponses disabled',
        to=[user.email],
        body='\n\n'.join(paragraphs),
        reply_to=['noreply@gchat.simon.codes'],
    )
    email.send(fail_silently=False)
    logger.info("sent trial expiry email to %r", user.email)


def save_init_license(user):
    license = License.objects.create(user=user, trial_start=timezone.now())
    CurrentLicense.objects.create(user=user, license=license)


def get_default_payment_method(customer):
    return [m for m in customer.payment_methods if m.default][0]


def transition_license(license, new_fields):
    prev_was_active = license.is_active

    license.id = None  # django will create a new row
    for (field, val) in new_fields.items():
        setattr(license, field, val)
    license.save()
    new_is_active = license.is_active

    user = license.user
    user.currentlicense.license = license
    user.currentlicense.save()

    logger.info("current license for %s now %r", user.id, serializers.serialize("json", [license]))

    if prev_was_active and not new_is_active:
        _transition_autoresponses('stop', user)
    elif not prev_was_active and new_is_active:
        _transition_autoresponses('restart', user)

    return license


@transaction.atomic
def sync_license(license, bt_subscription):
    has_changed = False

    logger.info("comparing license %r to bt sub %r", serializers.serialize("json", [license]), bt_subscription)
    if license.bt_subscription_id != bt_subscription.id:
        logger.info("subscription id has changed")
        has_changed = True
    if license.bt_status != bt_subscription.status:
        logger.info("subscription status has changed")
        has_changed = True
        if bt_subscription.status == braintree.Subscription.Status.Canceled:
            bt_subscription.id = ''

    if has_changed:
        transition_license(
            license,
            {
                'bt_subscription_id': bt_subscription.id,
                'bt_status': bt_subscription.status,
            }
        )
