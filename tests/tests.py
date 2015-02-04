from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from mapgroups.actions import create_map_group, join_map_group, \
    request_map_group_invitation
from mapgroups.models import MapGroup, MapGroupMember, ActivityLog, Invitation

MAPGROUP_CREATE_URL = 'mapgroups:create'
MAPGROUP_DETAIL_URL = 'mapgroups:detail'

def create_users():
    users = {
        'usr1': User.objects.create_user('usr1', email='usr1@example.com'),
        'usr2': User.objects.create_user('usr2', email='usr2@example.com'),
        'usr3': User.objects.create_user('usr3', email='usr3@example.com'),
        'usr4': User.objects.create_user('usr4', email='usr4@example.com'),
    }

    for u in users.values():
        u.set_password('abc')
        u.save()

    return users

class MapGroupTest(TestCase):
    def setUp(self):
        self.users = create_users()

    def test_get_absolute_url(self):
        mg = MapGroup(name='Swans swiftly swim', blurb='Fluttering Feathers',
                      owner=self.users['usr1'])
        mg.save()
        url = mg.get_absolute_url()
        self.assertEqual(url, reverse(MAPGROUP_DETAIL_URL,
                                      args=(mg.id, mg.slug)))
        mg.delete()


class CreateMapGroupTest(TestCase):
    """User creates a map group.
    """
    def setUp(self):
        self.users = create_users()
        self.mg, self.member = create_map_group("Turtles Travel Together",
                                                self.users['usr1'],
                                                blurb="<b>I like turtles</b>")

    def test_group_has_owner(self):
        mg = MapGroup.objects.get(pk=self.mg.pk)
        self.assertEqual(mg.owner.pk, self.users['usr1'].pk)

    def test_group_name(self):
        mg = MapGroup.objects.get(pk=self.mg.pk)
        self.assertEqual(mg.name, "Turtles Travel Together")

    def test_group_blurb(self):
        mg = MapGroup.objects.get(pk=self.mg.pk)
        self.assertEqual(mg.blurb, "<b>I like turtles</b>")

    def test_owner_is_manager(self):
        mg = MapGroup.objects.get(pk=self.mg.pk)
        manager = MapGroupMember.objects.get(user=self.users['usr1'])

        self.assertEqual(manager.map_group, mg)
        self.assertTrue(manager.is_manager)

    def test_group_created_permission_group(self):
        self.assertTrue(Group.objects.filter(name=self.mg.permission_group_name()).exists())

    def test_group_owner_in_permission_group(self):
        pgname = self.mg.permission_group_name()
        self.assertTrue(self.mg.owner.groups.filter(name=pgname).exists())

    def tearDown(self):
        for user in self.users.values():
            user.delete()

        TestCase.tearDown(self)


class CreateMapGroupViewTest(TestCase):
    """Test the form view
    """
    def setUp(self):
        self.users = create_users()

    def test_get(self):
        c = Client()
        c.login(username=self.users['usr1'].username, password='abc')
        resp = c.get(reverse(MAPGROUP_CREATE_URL))
        self.assertEqual(resp.status_code, 200)

    def test_get_unauth(self):
        c = Client()
        resp = c.get(reverse(MAPGROUP_CREATE_URL))

        # if this were being tested in the context of a full application,
        # we self.assertRedirects(expected_url=login_url, ...)
        # For now we'll just look for a temporary redirect.
        self.assertEqual(resp.status_code, 302)

    def test_create_group(self):
        c = Client()
        c.login(username=self.users['usr1'].username, password='abc')

        post_data = {
            'name': 'Clams claim countryside',
            'blurb': 'Not oysters, but clams',
            'is_open': True,
        }

        resp = c.post(reverse(MAPGROUP_CREATE_URL), post_data)
        # Looking for assertRedirects to a particular MapGroup
        self.assertEqual(resp.status_code, 302)



    def test_create_group_unauth(self):
        c = Client()

        post_data = {
            'name': 'Clams claim countryside',
            'blurb': 'Not oysters, but clams',
            'is_open': True,
        }

        resp = c.post(reverse(MAPGROUP_CREATE_URL), post_data)
        self.assertEqual(resp.status_code, 302)


class MapGroupDetailTest(TestCase):
    pass


class MapGroupListTest(TestCase):
    pass

class JoinMapGroupTest(TestCase):
    """User joins a map group.
    """

    def setUp(self):
        self.users = create_users()
        open_group, _ = create_map_group('Salmon swiftly swam', self.users['usr1'],
                                         open=True)
        self.open_group = open_group
        closed_group, _ = create_map_group('Gulls gently glide',
                                           self.users['usr2'], open=False)
        self.closed_group = closed_group

    def test_join_open_group(self):
        # Joining a map group if you are already a member returns your
        # membership card.
        result = join_map_group(self.users['usr1'], self.open_group)
        self.assertIsInstance(result, MapGroupMember)

        # If it's an open group, then joining will succeed
        result = join_map_group(self.users['usr2'], self.open_group)
        self.assertIsInstance(result, MapGroupMember)
        self.assertEqual(result.user, self.users['usr2'])

        log = ActivityLog.objects.filter(group=self.open_group, admin=True,
                                         associated_user=self.users['usr2'])
        self.assertTrue(log.exists())


    def test_join_closed_group(self):
        # Verify that we can't join a closed group
        result = join_map_group(self.users['usr1'], self.closed_group)
        self.assertIsNone(result)

        invite, new = request_map_group_invitation(self.users['usr1'],
                                                   self.closed_group)

        self.assertIsInstance(invite, Invitation)
        self.assertTrue(new)

        log = ActivityLog.objects.filter(group=self.closed_group, admin=True,
                                         associated_user=self.users['usr1'])
        self.assertTrue(log.exists())

        # request the invitation again
        invite2, new = request_map_group_invitation(self.users['usr1'],
                                                    self.closed_group)
        self.assertEqual(invite2, invite)
        self.assertFalse(new)

        # try to request an invite for an existing member
        invite, new = request_map_group_invitation(self.users['usr2'],
                                                   self.closed_group)
        self.assertIsNone(invite)
        self.assertFalse(new)


class InviteUserToGroupTest(TestCase):
    """Group manager invites someone via email to join a group.
    """


class GroupMembershipTest(TestCase):
    """Features of membership (banning, etc.)
    """


class GroupLogTest(TestCase):
    """Make sure the activity log works.
    """

