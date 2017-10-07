from django.db import models
from django.contrib.auth.models import User

from oauth2client.contrib.django_util.models import CredentialsField


class GoogleCredential(models.Model):
    credentials = CredentialsField()
    user = models.ForeignKey(User)
    email = models.EmailField(unique=True)

    def __unicode__(self):
        return self.email


class AutoResponse(models.Model):
    response = models.TextField()
    user = models.ForeignKey(User)
    throttle_mins = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='rate limit (minutes)',
        help_text=("After autoresponding, wait this many minutes before responding again to the same contact."
                   ' Setting to 0 will respond to every message.'))

    credentials = models.OneToOneField(
        GoogleCredential,
        verbose_name="autorespond account")

    email_notifications = models.BooleanField(
        default=False,
        help_text="Enable to receive an email when an autoresponse is sent.")

    admin_disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return "<AutoResponse email:%s>" % self.credentials.email
