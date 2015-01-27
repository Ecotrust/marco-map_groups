from django.contrib.auth.models import User
from django.test import TestCase
from map_groups.models import MapGroup, MapGroupMember


def create_users():
    u = User()
    u.username='gadmin'
    u.first_name='G'
    u.last_name='Admin'
    u.set_password('ABC')
    u.save()

    return {
        'gadmin': u,
    }


class CreateMapGroupTest(TestCase):
    """User creates a map group.
    """
    def setUp(self):
        self.users = create_users()

        mg = MapGroup()
        mg.name = "Turtles Travel Together"

        member = MapGroupMember()
        member.is_owner = True
        member.is_manager = True
        member.user = self.users['gadmin']
        member.group = mg

        mg.owner = member

        mg.save()




    def testAbc(self):
        self.assertFalse("Failed")

    def tearDown(self):
        TestCase.tearDown(self)


class JoinMapGroupTest(TestCase):
    """User joins a map group.
    """


class InviteUserToGroupTest(TestCase):
    """Group manager invites someone via email to join a group.
    """



class GroupMembershipTest(TestCase):
    """Features of membership (banning, etc.)
    """


class GroupLogTest(TestCase):
    """Make sure the activity log works.
    """

