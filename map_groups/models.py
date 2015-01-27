from django.contrib.auth.models import User
from django.db import models


class MapGroup(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey('MapGroupMember')
#     icon = models.URLField()
#     image = models.URLField()
    group_blurb = models.CharField(max_length=512)    # how long?
    
    invitation_required = models.BooleanField(default=False, help_text=("If "
        "true, users must be invited or request an invitation (approval) to "
        "join this group"))
    
    def __str__(self):
        return "Map Group %s" % self.name
    

class MapGroupMember(models.Model):
    user = models.ForeignKey(User)
    map_group = models.ForeignKey(MapGroup)

    date_joined = models.DateTimeField(auto_now_add=True)
    
    # permissions
    is_owner = models.BooleanField(default=False, help_text=("If true, this " 
                                   "user is the group's creator."))
    is_manager = models.BooleanField(default=False, help_text=("If true, this "
                                     "user may perform admin actions on this "
                                     "group"))

    # user-group-specific preferences
    show_real_name = models.BooleanField(default=False)


class FeaturedGroups(models.Model):
    rank = models.PositiveIntegerField()
    map_group = models.ForeignKey(MapGroup)


class ActivityLog(models.Model):
    """Record for events that have happened in this group.
    """
    
    group = models.ForeignKey(MapGroup)
    message = models.CharField(max_length=256)
    for_managers = models.BooleanField(default=False, help_text=("If true, this"
                                       " message is only viewable by managers."))
    associated_user = models.ForeignKey(User, null=True, blank=True, 
                                        help_text=("The user this message is "
                                                   "associated with, if any."))
    


class Invitation(models.Model):
    """A model to store user requests to join an invitation-only group, or 
    admin invitations to a user.
    
    User selects "Join group"
    If that group is "open"
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(MapGroup)
#     message = models.CharField(max_length=512, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
     


class EmailInvitation(models.Model):
    pass

