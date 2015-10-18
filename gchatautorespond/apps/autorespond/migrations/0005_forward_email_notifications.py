# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0004_auto_20150603_0328'),
    ]

    operations = [
        migrations.AddField(
            model_name='forward',
            name='email_notifications',
            field=models.BooleanField(default=False),
        ),
    ]
