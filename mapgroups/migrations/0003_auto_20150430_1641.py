# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import mapgroups.models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('mapgroups', '0002_auto_20150427_1928'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapgroup',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 30, 16, 41, 46, 86069, tzinfo=utc), auto_created=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='mapgroup',
            name='image',
            field=models.ImageField(height_field='image_height', width_field='image_width', null=True, upload_to=mapgroups.models.map_group_image_path, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mapgroup',
            name='image_height',
            field=models.PositiveSmallIntegerField(default=0, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mapgroup',
            name='image_width',
            field=models.PositiveSmallIntegerField(default=0, null=True, blank=True),
            preserve_default=True,
        ),
    ]
