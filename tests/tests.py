from django.contrib import auth
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import Client

from mapgroups.actions import create_map_group, join_map_group, \
    request_map_group_invitation
from mapgroups.models import MapGroup, MapGroupMember, ActivityLog, Invitation, \
    FeaturedGroups


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
        self.mg = MapGroup(name='Swans swiftly swim', blurb='Fluttering Feathers',
                           owner=self.users['usr1'])
        self.mg.save()

    def test_get_absolute_url(self):
        url = self.mg.get_absolute_url()
        self.assertEqual(url, reverse(MAPGROUP_DETAIL_URL,
                                      args=(self.mg.id, self.mg.slug)))

    def test_map_group_has_anonymous_member(self):
        c = Client()
        anon = auth.get_user(c)
        self.assertTrue(anon.is_anonymous())
        self.assertFalse(self.mg.has_member(anon))


class FeaturedMapGroupTest(TestCase):
    def setUp(self):
        self.users = create_users()
        self.mg1 = MapGroup(name='Swans swiftly swim', blurb='Fluttering Feathers',
                            owner=self.users['usr1'])
        self.mg1.save()

        self.mg2 = MapGroup(name='Octopus Openly Outrageous', blurb='Somany Suckers',
                            owner=self.users['usr2'])
        self.mg2.save()
        self.mg2.featuredgroups_set.create(rank=1)

    def test_managers(self):
        self.assertEqual(MapGroup.objects.all().count(), 2)
        self.assertEqual(MapGroup.not_featured.all().count(), 1)
        self.assertEqual(MapGroup.featured.all().count(), 1)

    def test_rank_unique(self):
        def c():
            self.mg1.featuredgroups_set.create(rank=1)

        self.assertRaises(IntegrityError, c)

    def test_fk_unique(self):
        def c():
            FeaturedGroups.objects.create(rank=13, map_group=self.mg2)

        self.assertRaises(IntegrityError, c)


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
        self.assertTrue(
            Group.objects.filter(name=self.mg.permission_group_name()).exists())

    def test_group_owner_in_permission_group(self):
        pgname = self.mg.permission_group_name()
        self.assertTrue(self.mg.owner.groups.filter(name=pgname).exists())

    def tearDown(self):
        for user in self.users.values():
            user.delete()

        TestCase.tearDown(self)


class EditMapGroupTest(TestCase):
    """User creates a map group.
    """

    def setUp(self):
        self.users = create_users()
        self.mg, self.member = create_map_group("Turtles Travel Together",
                                                self.users['usr1'],
                                                blurb="<b>I like turtles</b>",
                                                open=True)

    def test_anonymous_users_cant_edit(self):
        c = Client()
        resp = c.get(reverse('mapgroups:edit', kwargs={'pk': self.mg.pk,
                                                       'slug': self.mg.slug}))
        self.assertEqual(resp.status_code, 302)

    def test_non_owners_cant_edit(self):
        c = Client()
        self.assertTrue(c.login(username=self.users['usr2'].username,
                                password='abc'))

        resp = c.get(reverse('mapgroups:edit', kwargs={'pk': self.mg.pk,
                                                       'slug': self.mg.slug}))
        self.assertEqual(resp.status_code, 404)

    def test_owner_can_edit(self):
        c = Client()
        self.assertTrue(c.login(username=self.users['usr1'].username,
                                password='abc'))

        resp = c.get(reverse('mapgroups:edit', kwargs={'pk': self.mg.pk,
                                                       'slug': self.mg.slug}))
        self.assertEqual(resp.status_code, 200)

    def test_edit(self):
        c = Client()
        self.assertTrue(c.login(username=self.users['usr1'].username,
                                password='abc'))

        # add some members to test renaming
        join_map_group(self.users['usr2'], self.mg)
        join_map_group(self.users['usr3'], self.mg)
        self.assertTrue(self.users['usr2'].groups.filter(name=self.mg.permission_group_name()).exists())
        self.assertTrue(self.users['usr3'].groups.filter(name=self.mg.permission_group_name()).exists())

        data = {
            'name': 'Tarantula Tuesdays',
            'blurb': "It's totally not creepy",
            'is_open': False, # you must be *invited* to tarantula tuesdays
        }

        url = reverse('mapgroups:edit', kwargs={'pk': self.mg.pk,
                                                'slug': self.mg.slug})
        resp = c.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.status_code, 302)

        mg = MapGroup.objects.get(pk=self.mg.pk)
        self.assertEqual(mg.name, data['name'])
        self.assertEqual(mg.blurb, data['blurb'])
        self.assertEqual(mg.is_open, data['is_open'])
        self.assertEqual(mg.owner, self.users['usr1'])

        old_pg = Group.objects.filter(name=self.mg.permission_group_name())
        self.assertFalse(old_pg.exists(), "Old permission group wasn't deleted")
        pg = Group.objects.filter(name=mg.permission_group_name())
        self.assertTrue(pg.exists(), "New permission group doesn't exist")

        self.assertTrue(mg.owner.groups.filter(name=mg.permission_group_name()).exists())
        self.assertTrue(self.users['usr2'].groups.filter(name=mg.permission_group_name()).exists())
        self.assertTrue(self.users['usr3'].groups.filter(name=mg.permission_group_name()).exists())

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
        open_group, _ = create_map_group('Salmon swiftly swam',
                                         self.users['usr1'],
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

        # Make sure the user gets added to the permission group
        pgroup_name = self.open_group.permission_group_name()
        user_pgroup = self.users['usr1'].groups.filter(name=pgroup_name)
        self.assertTrue(user_pgroup.exists())

        # If it's an open group, then joining will succeed
        result = join_map_group(self.users['usr2'], self.open_group)
        self.assertIsInstance(result, MapGroupMember)
        self.assertEqual(result.user, self.users['usr2'])

        # Make sure the user gets added to the permission group
        pgroup_name = self.open_group.permission_group_name()
        user_pgroup = self.users['usr2'].groups.filter(name=pgroup_name)
        self.assertTrue(user_pgroup.exists())


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


class JoinMapGroupActionViewTest(TestCase):
    def setUp(self):
        self.users = create_users()
        open_group, _ = create_map_group('Salmon swiftly swam',
                                         self.users['usr1'],
                                         open=True)
        self.open_group = open_group
        closed_group, _ = create_map_group('Gulls gently glide',
                                           self.users['usr2'], open=False)
        self.closed_group = closed_group

    def test_join_open_group_anon(self):
        c = Client()
        openg_url = reverse('mapgroups:join', args=(self.open_group.pk,
                                                    self.open_group.slug))
        resp = c.post(openg_url, {})
        self.assertEqual(resp.status_code, 302) # redirect to login

    def test_join_open_group(self):
        c = Client()
        c.login(username=self.users['usr2'].username, password='abc')
        openg_url = reverse('mapgroups:join', args=(self.open_group.pk,
                                                    self.open_group.slug))
        resp = c.post(openg_url, {}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.open_group.has_member(self.users['usr2']))


class InviteUserToGroupTest(TestCase):
    """Group manager invites someone via email to join a group.
    """


class GroupMembershipTest(TestCase):
    """Features of membership (banning, etc.)
    """


class GroupLogTest(TestCase):
    """Make sure the activity log works.
    """

