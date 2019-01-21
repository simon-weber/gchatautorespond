# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0017_autoresponse_disable_responses'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoresponse',
            name='admin_override_email',
            field=models.TextField(help_text=b'A different user-provided email to receive notifications.', blank=True),
        ),
    ]
