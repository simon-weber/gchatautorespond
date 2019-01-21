# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0016_autoresponse_status_detection'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoresponse',
            name='disable_responses',
            field=models.BooleanField(default=False, help_text=b'Enable to never autorespond (overriding other settings). Email notifications may still be sent.'),
        ),
    ]
