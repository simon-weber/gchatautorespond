# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('autorespond', '0005_forward_email_notifications'),
    ]

    operations = [
        migrations.RenameModel('Forward', 'AutoResponse')
    ]
