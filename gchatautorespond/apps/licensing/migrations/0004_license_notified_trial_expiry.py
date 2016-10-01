# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licensing', '0003_auto_20160924_2340'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='notified_trial_expiry',
            field=models.BooleanField(default=False),
        ),
    ]
