# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=256)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('admin', models.BooleanField(default=False, help_text=b'If true, this message is only viewable by managers.')),
                ('associated_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text=b'The user this message is associated with, if any.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('to_address', models.EmailField(max_length=75)),
                ('invite_code', models.CharField(max_length=32)),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FeaturedGroups',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rank', models.PositiveIntegerField(unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=512, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('blurb', models.CharField(max_length=512)),
                ('is_open', models.BooleanField(default=False, help_text=b'If false, users must be invited or request to join this group')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('permission_group', models.ForeignKey(to='auth.Group', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapGroupMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('is_manager', models.BooleanField(default=False, help_text=b'If true, this user may perform admin actions on this group')),
                ('show_real_name', models.BooleanField(default=False)),
                ('map_group', models.ForeignKey(to='mapgroups.MapGroup')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='mapgroupmember',
            unique_together=set([('user', 'map_group')]),
        ),
        migrations.AddField(
            model_name='invitation',
            name='group',
            field=models.ForeignKey(to='mapgroups.MapGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invitation',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='featuredgroups',
            name='map_group',
            field=models.ForeignKey(to='mapgroups.MapGroup', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailinvitation',
            name='invited_by',
            field=models.ForeignKey(to='mapgroups.MapGroupMember'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailinvitation',
            name='map_group',
            field=models.ForeignKey(to='mapgroups.MapGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activitylog',
            name='group',
            field=models.ForeignKey(to='mapgroups.MapGroup'),
            preserve_default=True,
        ),
    ]
