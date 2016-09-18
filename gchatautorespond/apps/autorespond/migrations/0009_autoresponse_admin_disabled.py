# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0008_auto_20151017_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoresponse',
            name='admin_disabled',
            field=models.BooleanField(default=False),
        ),
    ]
