import django
django.setup()

import datetime
import logging

import braintree

from gchatautorespond.apps.licensing.lib import (
    sync_license,
    transition_license,
    notify_of_trial_expiry
)
from gchatautorespond.apps.licensing.models import CurrentLicense

logger = logging.getLogger('gchatautorespond.sync_licenses')

if __name__ == '__main__':
    try:
        logger.info('running')
        for currentlicense in CurrentLicense.objects.all():
            license = currentlicense.license
            if license.bt_subscription_id:
                # Sync braintree subscriptions.
                subscription = braintree.Subscription.find(license.bt_subscription_id)
                sync_license(license, subscription)
            elif ((not license.is_active
                   and not license.notified_trial_expiry
                   and datetime.datetime.now() < license.trial_start + (license.TRIAL_LENGTH * 2))):
                # Notify users of trial expiry if we haven't before and the trial expired recently.
                # The recency check avoids sending an email to a user who upgraded while in a trial,
                # then cancels much later. This could be done better by storing the last time we checked
                # the license, but this case should be pretty rare.
                notify_of_trial_expiry(license.user)
                transition_license(license, {'notified_trial_expiry': True})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
