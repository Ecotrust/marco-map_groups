# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mapgroups', '0003_auto_20150430_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapgroup',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=True,
        ),
    ]
