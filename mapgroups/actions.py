from django.contrib.auth.models import Group
from mapgroups.models import MapGroup, MapGroupMember, Invitation, ActivityLog


def join_map_group(user, group):
    """Have a user try to join a group.
    @returns MapGroupMember if successful, None if not
    @type group MapGroup
    """
    if group.has_member(user):
        return user.mapgroupmember_set.get(map_group=group)

    if not group.is_open:
        # Must request an invite
        return None

    # TODO: get user preference for show_real_name
    member = MapGroupMember.objects.create(user=user, map_group=group,
                                           is_manager=False,
                                           show_real_name=False)
    member.save()

    pg = Group.objects.get(name=group.permission_group_name())
    user.groups.add(pg)

    log = ActivityLog()
    log.associated_user = user
    log.admin = True
    log.group = group
    log.message = "Invitation Request"
    log.save()

    return member


def request_map_group_invitation(user, group, message=''):
    """Send a request to join a closed group.
    """
    if group.has_member(user):
        return None, False

    invite, new = Invitation.objects.get_or_create(user=user, group=group)

    if new:
        invite.message = message
        invite.save()

        log = ActivityLog()
        log.associated_user = user
        log.admin = True
        log.group = group
        log.message = "Invitation Request"
        log.save()

    return invite, new

