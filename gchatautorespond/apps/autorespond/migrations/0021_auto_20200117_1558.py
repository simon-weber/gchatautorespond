# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-01-17 15:58
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0020_auto_20190722_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoresponse',
            name='throttle_mins',
            field=models.PositiveSmallIntegerField(default=5, help_text='After autoresponding, wait this many minutes before responding again to the same contact. Setting to 0 will respond to every message.', validators=[django.core.validators.MinValueValidator(1)], verbose_name='rate limit (minutes)'),
        ),
    ]