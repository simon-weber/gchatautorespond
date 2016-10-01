# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CurrentLicense',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('trial_start', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_disabled', models.BooleanField(default=False)),
                ('note', models.TextField(blank=True)),
                ('bt_status', models.TextField(blank=True)),
                ('bt_subscription_id', models.TextField(blank=True)),
                ('bt_customer_id', models.TextField(blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='currentlicense',
            name='license',
            field=models.OneToOneField(to='licensing.License'),
        ),
        migrations.AddField(
            model_name='currentlicense',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
    ]
