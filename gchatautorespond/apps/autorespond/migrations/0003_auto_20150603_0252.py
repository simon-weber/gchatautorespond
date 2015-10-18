# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0002_auto_20150603_0222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googlecredential',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
    ]
