# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0007_auto_20151017_2041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoresponse',
            name='credentials',
            field=models.OneToOneField(verbose_name=b'autorespond account', to='autorespond.GoogleCredential'),
        ),
    ]
