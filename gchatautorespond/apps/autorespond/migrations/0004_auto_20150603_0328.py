# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0003_auto_20150603_0252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forward',
            name='credentials',
            field=models.OneToOneField(to='autorespond.GoogleCredential'),
        ),
    ]
