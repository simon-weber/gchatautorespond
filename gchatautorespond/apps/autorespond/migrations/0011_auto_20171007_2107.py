# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0010_autoresponse_throttle_mins'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoresponse',
            name='throttle_mins',
            field=models.PositiveSmallIntegerField(default=5, help_text=b'After autoresponding, wait this many minutes before responding again to the same contact. Setting to 0 will respond to every message.', verbose_name=b'rate limit (minutes)'),
        ),
    ]
