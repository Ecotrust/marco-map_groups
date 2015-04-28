from io import StringIO
import io
import json
from django.contrib import auth
from django.core.files.uploadedfile import InMemoryUploadedFile, \
    SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.http import JsonResponse
from django.test import TestCase
from django.test.client import Client

from mapgroups.actions import join_map_group, \
    request_map_group_invitation, leave_non_owned_map_group, \
    delete_owned_map_group
from mapgroups.models import MapGroup, MapGroupMember, ActivityLog, Invitation, \
    FeaturedGroups, map_group_image_path


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

def tiny_image():
    """Return an image file-like, suitable for testing image uploads.
    Currently you're getting a 42 byte transparent 1x1 gif.

    """
    tiny_gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;'
    tiny_gif_file = io.BytesIO(tiny_gif)
    return tiny_gif_file


class MiscTests(TestCase):
    def test_map_group_image_path(self):
        name = map_group_image_path(None, 'blah.jpg')
        path_len = len('group_images')
        path_len += len('/')
        path_len += 8   # for the date stamp
        path_len += len('/')
        path_len += 32  # for the file name hash
        path_len += 4   # '.' + 'jpg'

        self.assertEqual(len(name), path_len)


class MapGroupTest(TestCase):
    def setUp(self):
        self.users = create_users()
        self.mg, self.member = MapGroup.objects.create("Swans swiftly swim",
            self.users['usr1'], blurb="<b>Fluttering Feathers</b>")
        self.mg.save()

    def test_get_absolute_url(self):
        url = self.mg.get_absolute_url()
        self.assertEqual(url, reverse('mapgroups:detail',
                                      args=(self.mg.id, self.mg.slug)))

    def test_map_group_has_anonymous_member(self):
        c = Client()
        anon = auth.get_user(c)
        self.assertTrue(anon.is_anonymous())
        self.assertFalse(self.mg.has_member(anon))

    def test_permission_group_name(self):
        m = MapGroup(name='x' * 90)
        self.assertEqual(len(m._permission_group_name()), 80)

        m = MapGroup(name='x' * 10)
        self.assertEqual(len(m._permission_group_name()), 18)


class FeaturedMapGroupTest(TestCase):
    def setUp(self):
        self.users = create_users()
        self.mg1, self.mg1_owner = MapGroup.objects.create(
                                        name='Swans swiftly swim',
                                        blurb='Fluttering Feathers',
                                        owner=self.users['usr1'])

        self.mg2, self.mg2_owner = MapGroup.objects.create(
                                           name='Octopus Openly Outrageous',
                                           blurb='Somany Suckers',
                                           owner=self.users['usr2'])
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
        self.mg, self.member = MapGroup.objects.create("Turtles Travel Together",
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

    def test_group_owner_in_permission_group(self):
        pgname = self.mg.permission_group.name
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
        self.mg, self.member = MapGroup.objects.create("Turtles Travel Together",
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
        # TODO: test group membership the right way
        self.assertTrue(self.users['usr2'].groups.filter(name=self.mg.permission_group.name).exists())
        self.assertTrue(self.users['usr3'].groups.filter(name=self.mg.permission_group.name).exists())

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

        old_pg = Group.objects.filter(name=self.mg.permission_group.name)
        self.assertFalse(old_pg.exists(), "Old permission group wasn't deleted")
        pg = Group.objects.filter(name=mg.permission_group.name)
        self.assertTrue(pg.exists(), "New permission group doesn't exist")

        self.assertTrue(mg.owner.groups.filter(name=mg.permission_group.name).exists())
        self.assertTrue(self.users['usr2'].groups.filter(name=mg.permission_group.name).exists())
        self.assertTrue(self.users['usr3'].groups.filter(name=mg.permission_group.name).exists())

    def tearDown(self):
        for user in self.users.values():
            user.delete()

        TestCase.tearDown(self)


class MapGroupPreferencesTest(TestCase):
    def setUp(self):
        self.users = create_users()
        self.mg, self.member = MapGroup.objects.create("Turtles Travel Together",
                                                       self.users['usr1'],
                                                       blurb="<b>I like turtles</b>",
                                                       open=True)

    def test_post_redirects(self):
        u = self.users['usr1']
        c = Client()
        self.assertTrue(c.login(username=u.username, password='abc'))
        url = reverse('mapgroups:preferences', args=(self.mg.id, self.mg.slug))
        detail_url = reverse('mapgroups:detail', args=(self.mg.id, self.mg.slug))

        response = c.post(url, {'show_real_name': True})
        self.assertRedirects(response, detail_url)

    def test_form_sets_real_name(self):
        u = self.users['usr1']
        c = Client()
        self.assertTrue(c.login(username=u.username, password='abc'))

        url = reverse('mapgroups:preferences', args=(self.mg.id, self.mg.slug))
        response = c.post(url, {'show_real_name': not self.member.show_real_name})

        member = self.mg.get_member(self.users['usr1'])
        self.assertNotEqual(member.show_real_name, self.member.show_real_name)

    def test_non_member_cant_change_preferences(self):
        # Anonymous users would be redirected to the login page
        u = self.users['usr2']
        c = Client()
        self.assertTrue(c.login(username=u.username, password='abc'))

        url = reverse('mapgroups:preferences', args=(self.mg.id, self.mg.slug))
        response = c.post(url, {'show_real_name': True})
        self.assertEqual(response.status_code, 404)


class CreateMapGroupViewTest(TestCase):
    """Test the form view
    """

    def setUp(self):
        self.users = create_users()

    def test_get(self):
        c = Client()
        c.login(username=self.users['usr1'].username, password='abc')
        resp = c.get(reverse('mapgroups:create'))
        self.assertEqual(resp.status_code, 200)

    def test_get_unauth(self):
        c = Client()
        resp = c.get(reverse('mapgroups:create'))

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
            'image': SimpleUploadedFile('tiny.gif', tiny_image().read(), 'image/gif')
        }

        resp = c.post(reverse('mapgroups:create'), post_data)
        # Looking for assertRedirects to a particular MapGroup
        self.assertEqual(resp.status_code, 302)


    def test_create_group_unauth(self):
        c = Client()

        post_data = {
            'name': 'Clams claim countryside',
            'blurb': 'Not oysters, but clams',
            'is_open': True,
        }

        resp = c.post(reverse('mapgroups:create'), post_data)
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
        open_group, _ = MapGroup.objects.create('Salmon swiftly swam',
                                                self.users['usr1'],
                                                open=True)
        self.open_group = open_group
        closed_group, _ = MapGroup.objects.create('Gulls gently glide',
                                                  self.users['usr2'],
                                                  open=False)
        self.closed_group = closed_group

    def test_join_open_group(self):
        # Joining a map group if you are already a member returns your
        # membership card.
        result = join_map_group(self.users['usr1'], self.open_group)
        self.assertIsInstance(result, MapGroupMember)

        # Make sure the user gets added to the permission group
        pgroup_name = self.open_group.permission_group.name
        user_pgroup = self.users['usr1'].groups.filter(name=pgroup_name)
        self.assertTrue(user_pgroup.exists())

        # If it's an open group, then joining will succeed
        result = join_map_group(self.users['usr2'], self.open_group)
        self.assertIsInstance(result, MapGroupMember)
        self.assertEqual(result.user, self.users['usr2'])

        # Make sure the user gets added to the permission group
        pgroup_name = self.open_group.permission_group.name
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


class LeaveNonOwnedMapGroupTest(TestCase):
    """User leaves a map group that they don't own
    """

    def setUp(self):
        self.users = create_users()
        self.group, _ = MapGroup.objects.create('Salmon swiftly swam',
                                                self.users['usr1'], open=True)

    def test_leave_group(self):
        user = self.users['usr2']
        group = self.group
        result = join_map_group(user, group)
        self.assertIsInstance(result, MapGroupMember)

        self.assertTrue(group.has_member(user))
        self.assertTrue(group.permission_group.user_set.filter(pk=user.pk).exists())

        result = leave_non_owned_map_group(user, group)

        self.assertTrue(result)
        self.assertFalse(group.has_member(user))
        self.assertFalse(group.permission_group.user_set.filter(pk=user.pk).exists())


class DeleteOwnedMapGroupTest(TestCase):
    """A group owner deletes a map group that they own.
    """

    def setUp(self):
        self.users = create_users()

    def test_owner_delete_group(self):
        user = self.users['usr1']
        self.group1, _ = MapGroup.objects.create('Salmon swiftly swam',
                                                 user, open=True)

        gpk = self.group1.pk
        pgpk = self.group1.permission_group.pk

        result = delete_owned_map_group(user, self.group1)
        self.assertTrue(result)

        self.assertFalse(MapGroup.objects.filter(pk=gpk).exists())
        self.assertFalse(Group.objects.filter(pk=pgpk).exists())

    def test_nonowner_delete_group(self):
        user = self.users['usr1']
        self.group1, _ = MapGroup.objects.create('Salmon swiftly swam',
                                                 user, open=True)

        gpk = self.group1.pk
        pgpk = self.group1.permission_group.pk

        result = delete_owned_map_group(self.users['usr2'], self.group1)

        self.assertFalse(result)
        self.assertTrue(MapGroup.objects.filter(pk=gpk).exists())
        self.assertTrue(Group.objects.filter(pk=pgpk).exists())


class JoinMapGroupActionViewTest(TestCase):
    def setUp(self):
        self.users = create_users()
        open_group, _ = MapGroup.objects.create('Salmon swiftly swam',
                                                self.users['usr1'],
                                                open=True)
        self.open_group = open_group
        closed_group, _ = MapGroup.objects.create('Gulls gently glide',
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


class MapGroupMemberTest(TestCase):
    def setUp(self):
        pass

    def test_user_name_for_group(self):
        self.fail('Make sure this shows the correct username per group setting.')


class MapGroupRPCTest(TestCase):
    def setUp(self):
        self.users = create_users()
        self.mg, self.member = MapGroup.objects.create("Swans swiftly swim",
            self.users['usr1'], blurb="<b>Fluttering Feathers</b>")
        self.mg.save()

    def test_mp_820_anon_get_sharing_groups_works(self):
        c = Client()
        try:
            c.get(reverse('mapgroups:rpc:get_sharing_groups'))
        except AttributeError:
            self.fail("Get sharing groups anonymously failed (MP-820)")
    
    def test_get_sharing_groups_logged_in(self):
        c = Client()
        self.assertTrue(c.login(username=self.users['usr1'].username,
                                password='abc'))
        r = c.get(reverse('mapgroups:rpc:get_sharing_groups'))

        self.assertIsInstance(r, JsonResponse, "Didn't get a JsonResponse")
        try:
            data = json.loads(r.content)
        except ValueError:
            self.fail('Response was parsable not JSON')

        # User 1 should have a single sharing group
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        data = data[0]
        self.assertIn('group_name', data.keys())
        self.assertIn('group_slug', data.keys())
        self.assertIn('members', data.keys())

        # If new keys are added then modify the test
        self.assertEqual(len(data.keys()), 3)


