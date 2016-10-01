# -*- coding: utf-8 -*-
"""
A data migration to backfill licenses into existing users.
"""

from __future__ import unicode_literals

from django.db import migrations
from django.utils import timezone


def backfill_licenses(apps, schema_editor):
    CurrentLicense = apps.get_model("licensing", "CurrentLicense")
    License = apps.get_model("licensing", "License")
    User = apps.get_model("auth", "User")

    CurrentLicense.objects.all().delete()
    License.objects.all().delete()

    for user in User.objects.all():
        license = License.objects.create(user=user, trial_start=timezone.now())
        CurrentLicense.objects.create(user=user, license=license)


class Migration(migrations.Migration):

    dependencies = [
        ('licensing', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_licenses),
    ]
