# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autorespond', '0014_excludeduser_email_notifications'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bare_jid', models.CharField(max_length=256)),
                ('last_response_time', models.DateTimeField()),
                ('autorespond', models.ForeignKey(verbose_name=b'autorespond', to='autorespond.AutoResponse', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='lastresponse',
            unique_together=set([('autorespond', 'bare_jid')]),
        ),
        migrations.AlterIndexTogether(
            name='lastresponse',
            index_together=set([('autorespond', 'bare_jid')]),
        ),
    ]
