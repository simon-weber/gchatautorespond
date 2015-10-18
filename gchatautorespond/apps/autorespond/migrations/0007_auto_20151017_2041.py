# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0006_auto_20151017_0343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoresponse',
            name='credentials',
            field=models.OneToOneField(verbose_name=b'autorespond email', to='autorespond.GoogleCredential'),
        ),
        migrations.AlterField(
            model_name='autoresponse',
            name='email_notifications',
            field=models.BooleanField(default=False, help_text=b'Enable to receive an email when an autoresponse is sent.'),
        ),
    ]
