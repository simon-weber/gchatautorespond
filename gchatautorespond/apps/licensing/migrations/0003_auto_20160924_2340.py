# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licensing', '0002_backfill_licenses'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='license',
            name='admin_disabled',
        ),
        migrations.AddField(
            model_name='license',
            name='admin_override',
            field=models.CharField(blank=True, max_length=2, choices=[(b'DI', b'Disable'), (b'EN', b'Enable')]),
        ),
    ]
