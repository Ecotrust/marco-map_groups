"""
JSON-RPC endpoint for mapgroups.

SRH May-2015
"""

from rpc4django import rpcmethod
from django.conf import settings
from django.contrib.auth.models import Group
from mapgroups.models import MapGroup

@rpcmethod(login_required=True)
def get_sharing_groups(request):
    data = []
    for membership in request.user.mapgroupmember_set.all():
        group = membership.map_group
        members = [member.user_name_for_group()
                   for member in group.mapgroupmember_set.all()]
        members.sort()

        data.append({
            'group_name': group.name,
            'group_slug': group.permission_group.name,
            'members': members,
            'is_mapgroup': True,
        })
    for public_group in Group.objects.filter(name__in=settings.SHARING_TO_PUBLIC_GROUPS):
        data.append({
            'group_name': public_group.name,
            'group_slug': public_group.name,
            'members': [],
            'is_mapgroup': False,
        })

    return data

@rpcmethod(login_required=True)
def update_map_group(group_id, options, **kwargs):
    from django.shortcuts import get_object_or_404
    request = kwargs.get('request')
    mg = get_object_or_404(MapGroup, id=group_id, owner=request.user)
    changed = False

    if options.get('update_name'):
        mg.name = options['name']
        changed = True

    if options.get('update_blurb'):
        mg.blurb = options['blurb']
        changed = True

    if options.get('update_is_open'):
        mg.is_open = options['is_open']
        changed = True

    if changed:
        mg.save()

    return None
