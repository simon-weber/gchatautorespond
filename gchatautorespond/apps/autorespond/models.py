from django.db import models
from django.contrib.auth.models import User

from oauth2client.contrib.django_util.models import CredentialsField


class GoogleCredential(models.Model):
    credentials = CredentialsField()
    user = models.ForeignKey(User)
    email = models.EmailField(unique=True)

    def __str__(self):
        return "<GoogleCredential email:%s>" % self.email

    __repr__ = __str__


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

    status_detection = models.BooleanField(
        default=True,
        help_text="Disable to autorespond even when active in gmail or a mobile device.")

    disable_responses = models.BooleanField(
        default=False,
        help_text="Enable to never autorespond (overriding other settings). Email notifications may still be sent.")

    admin_disabled = models.BooleanField(default=False)
    admin_override_email = models.TextField(
        blank=True,
        help_text="A different user-provided email to receive notifications.",
    )

    def __str__(self):
        return "<AutoResponse email:%s>" % self.credentials.email

    __repr__ = __str__


class ExcludedUser(models.Model):
    name = models.CharField(
        max_length=128,
        help_text="A contact's full name as it appears when you chat with them. Capitalization is ignored.",
    )

    autorespond = models.ForeignKey(
        AutoResponse,
        verbose_name="autorespond")

    DEFAULT = 'DE'
    ALWAYS = 'AL'
    NEVER = 'NE'
    CHOICES = (
        (DEFAULT, 'default'),
        (ALWAYS, 'always'),
        (NEVER, 'never'),
    )
    email_notifications = models.CharField(
        max_length=2,
        choices=CHOICES,
        default=DEFAULT,
        help_text="Use 'always' or 'never' to override the email notification setting for this user.",
    )

    def __str__(self):
        return "<ExcludedUser '%s' for %s>" % (self.name, self.autorespond)

    __repr__ = __str__


class LastResponse(models.Model):
    autorespond = models.ForeignKey(
        AutoResponse,
        verbose_name="autorespond")

    bare_jid = models.CharField(
        max_length=256,
    )

    last_response_time = models.DateTimeField()

    class Meta(object):
        index_together = unique_together = [['autorespond', 'bare_jid']]
