# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0012_excludeduser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excludeduser',
            name='name',
            field=models.CharField(help_text=b"A contact's full name as it appears when you chat with them. Capitalization is ignored.", max_length=128),
        ),
    ]
