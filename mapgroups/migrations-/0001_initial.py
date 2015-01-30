# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

permission_groups_list = [
    'member',           # granted by login, equivalent to (not anonymous)
    'group_manager',    # admin permissions for a particular group
    'content_manager',  # create wagtail content (wagtail already has permissions for this)
    'data_manager',     # edit data catalog
    'data_admin',       # grant data_manager perm
    'content_admin',    # grant content_manager perm
    'site_admin',       # equivalent to is_superuser in user model
]

def create_groups(apps, schema_editor):
    # Group = apps.get_model("auth", "Group")

    # Group.objects.bulk_create()
    pass

def remove_groups(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups)
    ]
