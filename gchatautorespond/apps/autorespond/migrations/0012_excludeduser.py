# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0011_auto_20171007_2107'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExcludedUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('autorespond', models.ForeignKey(verbose_name=b'autorespond', to='autorespond.AutoResponse')),
            ],
        ),
    ]
