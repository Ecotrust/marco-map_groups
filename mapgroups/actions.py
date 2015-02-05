from mapgroups.models import MapGroup, MapGroupMember, Invitation, ActivityLog


def create_map_group(name, owner, open=False, blurb=''):
    """Creates a new map group with the specified options, owned by the
    specified user.

    @returns a tuple of (group, member)
    """

    mg = MapGroup()
    mg.name = name
    mg.blurb = blurb
    mg.owner = owner
    mg.is_open = open
    mg.save()

    member = MapGroupMember()
    member.user = owner
    member.is_manager = True
    member.map_group = mg
    member.save()

    # Introduce a weak dependency on Groups so the Madrona feature sharing
    # will continue to work.
    from django.contrib.auth.models import Group
    from features.registry import enable_sharing
    name = mg.permission_group_name()
    pg = Group.objects.create(name=name)
    enable_sharing(pg)

    # Add the owner to the new perm group
    owner.groups.add(pg)

    return mg, member


def join_map_group(user, group):
    """Have a user try to join a group.
    @returns MapGroupMember if successful, None if not
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

