from django.contrib.auth.models import User, Group
from django.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

class MapGroupManager(models.Manager):
    def get_queryset(self):
        qs = super(MapGroupManager, self).get_queryset()
        qs = qs.filter(featuredgroups__isnull=True)
        return qs


class MapGroupFeaturedManager(models.Manager):
    def get_queryset(self):
        qs = super(MapGroupFeaturedManager, self).get_queryset()
        qs = qs.filter(featuredgroups__isnull=False)
        return qs


class MapGroup(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    owner = models.ForeignKey(User)
#     icon = models.URLField()
#     image = models.URLField()
    blurb = models.CharField(max_length=512)    # how long?
    
    is_open = models.BooleanField(default=False, help_text=("If false, users "
        "must be invited or request to to join this group"))

    objects = models.Manager()
    not_featured = MapGroupManager()
    featured = MapGroupFeaturedManager()

    def __str__(self):
        return "Map Group '%s'" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(unicode(self.name))
        return super(MapGroup, self).save(*args, **kwargs)

    def rename(self, new_name):
        """Rename the mapgroup and it's associated permission group.
        """
        old_pg = get_object_or_404(Group, name=self.permission_group_name())
        self.name = new_name
        self.save()
        old_pg.name = self.permission_group_name()
        old_pg.save()

    def get_absolute_url(self):
        return reverse('mapgroups:detail', kwargs={'pk': self.pk,
                                                    'slug': self.slug})

    def has_member(self, user):
        """@type user User
        """
        if user.is_anonymous() or not user.is_active:
            return False
        return self.mapgroupmember_set.filter(user=user).exists()

    def permission_group_name(self):
        if not self.pk:
            raise Exception("Save the model before accessing the perm group name.")
        return '%s-%s' % (self.slug, self.pk)


class MapGroupMember(models.Model):
    user = models.ForeignKey(User)
    map_group = models.ForeignKey(MapGroup)

    date_joined = models.DateTimeField(auto_now_add=True)
    
    # permissions
    # is_owner = models.BooleanField(default=False, help_text=("If true, this "
    #                                "user is the group's creator."))
    is_manager = models.BooleanField(default=False, help_text=("If true, this "
                                     "user may perform admin actions on this "
                                     "group"))

    # user-group-specific preferences
    show_real_name = models.BooleanField(default=False)


class FeaturedGroupsManager(models.Manager):
    def get_queryset(self):
        return super(FeaturedGroupsManager, self).get_queryset().order_by('rank')


class FeaturedGroups(models.Model):
    rank = models.PositiveIntegerField(unique=True)
    # Note: unique FK here rather than 1:1, since the interface is a little
    # nicer in this case. You can say:
    # >>> mapgroup.featuredgroups_set.create(rank=4)
    # instead of:
    # >>> fg = FeaturedGroup.create(rank=4)
    # >>> mapgroup.featuredgroup = fg
    map_group = models.ForeignKey(MapGroup, unique=True)

    def __str__(self):
        return "#%d %s" % (self.rank, self.map_group.name)


class RecentActivityManager(models.Manager):
    def get_queryset(self):
        qs = super(RecentActivityManager, self).get_queryset()
        return qs.filter(date_created__lte=7)


# TODO: This isn't sufficient for admin messages
class ActivityLog(models.Model):
    """Record for events that have happened in this group.
    """
    
    group = models.ForeignKey(MapGroup)
    message = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    admin = models.BooleanField(default=False, help_text=("If true, this"
                                " message is only viewable by managers."))
    associated_user = models.ForeignKey(User, null=True, blank=True, 
                                        help_text=("The user this message is "
                                                   "associated with, if any."))

    recent = RecentActivityManager()
    objects = models.Manager()


class Invitation(models.Model):
    """A model to store user requests to join an invitation-only group, or 
    admin invitations to a user.
    
    User selects "Join group"
    If that group is "open"
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(MapGroup)
    message = models.CharField(max_length=512, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class EmailInvitation(models.Model):
    to_address = models.EmailField()
    map_group = models.ForeignKey(MapGroup)
    invite_code = models.CharField(max_length=32)
    invited_by = models.ForeignKey(MapGroupMember)
    date_sent = models.DateTimeField(auto_now_add=True)



