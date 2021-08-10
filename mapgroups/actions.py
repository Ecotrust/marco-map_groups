from django.contrib.auth.models import Group
import itertools
from mapgroups.models import MapGroup, MapGroupMember, Invitation, ActivityLog
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings


def join_map_group(user, group):
    """Have a user try to join a group.
    @returns MapGroupMember if successful, None if not
    @type group MapGroup
    """
    if group.get_member(user):
        membership = user.mapgroupmember_set.get(map_group=group)
        if membership.status in ['Pending','Accepted','Banned']:
            return membership

    if group.is_open:
        status='Accepted'
    else:
        # Must request an invite
        # return None
        status='Pending'

    # TODO: get user preference for show_real_name
    member, created = MapGroupMember.objects.get_or_create(user=user, map_group=group)

    if created:
        member.is_manager=False
        member.show_real_name=False

    member.status=status

    member.save()

    pg = group.permission_group
    user.groups.add(pg)

    if not group.is_open and status=='Pending':
        email_request_to_managers(member)

    log = ActivityLog()
    log.associated_user = user
    log.admin = True
    log.group = group
    log.message = "Invitation Request"
    log.save()

    return member

def email_request_to_managers(membership):
    user = membership.user
    group = membership.map_group
    managers = [x.user for x in group.mapgroupmember_set.filter(is_manager=True)]

    for manager in managers:
        context = {
            'manager_name': manager.get_short_name(),
            'user_preferred_name': user.get_short_name(),
            'user_full_name': user.get_full_name(),
            'group_name': group.name,
            'group_url': '{}{}'.format(settings.APP_URL, group.get_absolute_url()),
            'app_name': settings.APP_NAME,
            'team_name': settings.APP_TEAM_NAME,
            'team_email': settings.DEFAULT_FROM_EMAIL,
            'app_url': settings.APP_URL,
        }

        template = get_template('mapgroups/email/request_alert.txt')
        body_txt = template.render(context)

        # TODO: Make HTML template.
        body_html = body_txt
        #     template = get_template('accounts/mail/verify_email.html')
        #     body_html = template.render(context)

        manager.email_user('{}: New User Request'.format(group.name), body_txt, fail_silently=False)

def delete_owned_map_group(user, group):
    # can't delete a group unless you own it
    if group.owner != user:
        return False

    pgroup = group.permission_group
    group.delete()
    pgroup.delete()

    # foreign key cascaded deletes should take care of everything else.

    return True

def leave_non_owned_map_group(user, group):
    # can't leave a group if you own it
    if group.owner == user:
        return False

    # Can't leave a group that you're not an owner of
    if not group.has_member(user):
        return False

    group.mapgroupmember_set.get(user=user).delete()
    group.permission_group.user_set.remove(user)

    pgroup = group.permission_group

    # Unshare any features that were shared with the old group

    # TODO: Figure out a way to find all m2m models that are related to
    # Group, iterate over each, figure out if each item descends from 'Feature',
    # and then unshare each of those.
    # Right now, if we were to add a new kind of related feature that could
    # be shared, we'd have to remember to include it here by hand.
    items = itertools.chain(
        pgroup.scenarios_scenario_related.filter(user=user),
        pgroup.visualize_bookmark_related.filter(user=user),
        pgroup.scenarios_leaseblockselection_related.filter(user=user),
        pgroup.drawing_aoi_related.filter(user=user),
        pgroup.drawing_windenergysite_related.filter(user=user)
    )
    for item in items:
        item.unshare_with(pgroup)

    return True

def update_map_group_membership_status(user, membership, status):
    if membership.map_group.has_manager(user):
        membership.status=status
        membership.save()

        member = membership.user

        context = {
            'user_preferred_name': member.get_short_name(),
            'user_full_name': member.get_full_name(),
            'group_name': membership.map_group.name,
            'status': status,
            'group_url': '{}{}'.format(settings.APP_URL, membership.map_group.get_absolute_url()),
            'app_name': settings.APP_NAME,
            'team_name': settings.APP_TEAM_NAME,
            'team_email': settings.DEFAULT_FROM_EMAIL,
            'app_url': settings.APP_URL,
        }

        template = get_template('mapgroups/email/status_update.txt')
        body_txt = template.render(context)

        # TODO: Make HTML template.
        body_html = body_txt
        #     template = get_template('accounts/mail/verify_email.html')
        #     body_html = template.render(context)

        member.email_user('{}: Membership Status {}'.format(membership.map_group.name, status), body_txt, fail_silently=False)

        return True
    else:
        return False

def update_map_group_membership_manager(user, membership, is_manager):
    if membership.map_group.has_manager(user):
        membership.is_manager=is_manager
        membership.save()

        member = membership.user

        context = {
            'user_preferred_name': member.get_short_name(),
            'user_full_name': member.get_full_name(),
            'group_name': membership.map_group.name,
            'is_manager': is_manager,
            'group_url': '{}{}'.format(settings.APP_URL, membership.map_group.get_absolute_url()),
            'app_name': settings.APP_NAME,
            'team_name': settings.APP_TEAM_NAME,
            'team_email': settings.DEFAULT_FROM_EMAIL,
            'app_url': settings.APP_URL,
        }

        template = get_template('mapgroups/email/manager_status_update.txt')
        body_txt = template.render(context)

        # TODO: Make HTML template.
        body_html = body_txt
        #     template = get_template('accounts/mail/verify_email.html')
        #     body_html = template.render(context)

        member.email_user('{}: Manager Status Updated'.format(membership.map_group.name), body_txt, fail_silently=False)

        return True
    else:
        return False

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
