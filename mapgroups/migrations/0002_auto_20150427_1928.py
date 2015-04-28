# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mapgroups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapgroup',
            name='image',
            field=models.ImageField(height_field=b'image_height', width_field=b'image_width', null=True, upload_to=b'group_images/%Y%m%d/'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapgroup',
            name='image_height',
            field=models.PositiveSmallIntegerField(default=0, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapgroup',
            name='image_width',
            field=models.PositiveSmallIntegerField(default=0, null=True),
            preserve_default=True,
        ),
    ]
