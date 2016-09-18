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

    credentials = models.OneToOneField(
        GoogleCredential,
        verbose_name="autorespond account")

    email_notifications = models.BooleanField(
        default=False,
        help_text="Enable to receive an email when an autoresponse is sent.")

    admin_disabled = models.BooleanField(default=False)
