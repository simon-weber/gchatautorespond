# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0015_auto_20171014_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoresponse',
            name='status_detection',
            field=models.BooleanField(default=True, help_text=b'Disable to autorespond even when active in gmail or a mobile device.'),
        ),
    ]
