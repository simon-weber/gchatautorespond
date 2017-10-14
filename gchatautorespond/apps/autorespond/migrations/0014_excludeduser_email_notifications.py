# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0013_auto_20171011_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='excludeduser',
            name='email_notifications',
            field=models.CharField(default=b'DE', help_text=b"Use 'always' or 'never' to override the email notification setting for this user.", max_length=2, choices=[(b'DE', b'default'), (b'AL', b'always'), (b'NE', b'never')]),
        ),
    ]
