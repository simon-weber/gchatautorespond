import datetime

import braintree
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import enum


class License(models.Model):
    TRIAL_LENGTH = datetime.timedelta(days=7)
    BT_VALID_STATUSES = set([
        braintree.Subscription.Status.Active,
        braintree.Subscription.Status.Pending,
        # past due grace/cancellation is handled in braintree.
        braintree.Subscription.Status.PastDue,
    ])

    @enum.unique
    class Override(enum.Enum):
        ENABLE = 'EN'
        DISABLE = 'DI'

    user = models.ForeignKey(User)
    trial_start = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    admin_override = models.CharField(max_length=2,
                                      choices=((x.value, x.name.title()) for x in Override),
                                      blank=True)
    note = models.TextField(blank=True)
    bt_status = models.TextField(blank=True)
    bt_subscription_id = models.TextField(blank=True)  # blank if not created or cancelled
    bt_customer_id = models.TextField(blank=True)
    notified_trial_expiry = models.BooleanField(default=False)

    @property
    def is_trial(self):
        if self.admin_override:
            return False

        return self.trial_start > (timezone.now() - self.TRIAL_LENGTH)

    @property
    def is_active(self):
        if self.admin_override:
            return self.admin_override == License.Override.ENABLE.value

        return self.is_trial or self.bt_status in self.BT_VALID_STATUSES

    @property
    def trial_expire_date(self):
        return (self.trial_start + self.TRIAL_LENGTH).date()

    def __unicode__(self):
        return "<License %s user:%s active:%s>" % (self.id, self.user_id, self.is_active)


class CurrentLicense(models.Model):
    user = models.OneToOneField(User)
    license = models.OneToOneField(License)

    def __unicode__(self):
        return "<CurrentLicense %s user:%s license:%s>" % (self.id, self.user_id, self.license_id)
