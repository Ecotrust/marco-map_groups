import datetime
import uuid
from django.templatetags.static import static
import os
from django.contrib.auth.models import User, Group
from django.db import models
try:
    from django.urls import reverse
except (ModuleNotFoundError, ImportError):
    from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from features.registry import enable_sharing
from django.conf import settings

class MapGroupManager(models.Manager):
    def create(self, name, owner, open=False, blurb='', image=''):
        """Creates a new map group with the specified options, owned by the
        specified user.

        @returns a tuple of (group, member)
        """
        mg = MapGroup()
        mg.name = name
        mg.blurb = blurb
        mg.owner = owner
        mg.is_open = open
        mg.image = image

        # Introduce a dependency on Groups so the Madrona feature sharing
        # will continue to work.
        name = mg._permission_group_name()
        pg = Group.objects.create(name=name)
        enable_sharing(pg)

        mg.permission_group = pg
        mg.save()

        # Add the owner to the new perm group
        owner.groups.add(pg)

        member = MapGroupMember()
        member.user = owner
        member.is_manager = True
        member.map_group = mg
        member.save()

        return mg, member


class MapGroupNonFeaturedManager(models.Manager):
    def get_queryset(self):
        qs = super(MapGroupNonFeaturedManager, self).get_queryset()
        qs = qs.filter(featuredgroups__isnull=True)
        return qs


class MapGroupFeaturedManager(models.Manager):
    def get_queryset(self):
        qs = super(MapGroupFeaturedManager, self).get_queryset()
        qs = qs.filter(featuredgroups__isnull=False).order_by('rank')
        return qs


def map_group_image_path(instance, filename):
    """Callable to compute the image path for map groups.
    """
    name, ext = os.path.splitext(filename)
    name = uuid.uuid4().hex
    base = datetime.date.today().strftime('group_images/%Y%m%d')
    return '%s/%s%s' % (base, name, ext)



class MapGroup(models.Model):
    class Meta:
        app_label = "mapgroups"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
#     icon = models.URLField()
    image = models.ImageField(upload_to=map_group_image_path, #'group_images/%Y%m%d/',
                              width_field='image_width',
                              height_field='image_height', blank=True, null=True)
    image_width = models.PositiveSmallIntegerField(default=0, blank=True, null=True)
    image_height = models.PositiveSmallIntegerField(default=0, blank=True, null=True)
    blurb = models.CharField(max_length=512)    # how long?
    permission_group = models.ForeignKey(Group, unique=True, on_delete=models.CASCADE)

    is_open = models.BooleanField(default=False, help_text=("If false, users "
        "must be invited or request to join this group"))

    objects = MapGroupManager()
    not_featured = MapGroupNonFeaturedManager()
    featured = MapGroupFeaturedManager()

    _original_image_name = None


    def __init__(self, *args, **kwargs):
        super(MapGroup, self).__init__(*args, **kwargs)

        # Save a copy for later so we can see if it changed
        # The ImageField's file is bound to the model field itself, so to
        # delete the file on change, we must capture the file name and the
        # storage object.
        self._original_image_name = self.image.name

    def __str__(self):
        s = "Map Group '%s'" % self.name

        if self.featuredgroups_set.exists(): # then this model is featured
            s += ' (Featured, rank = %d)' % self.featuredgroups_set.get().rank
        return s

    def save(self, *args, **kwargs):
        self._process_uploaded_image()
        try:
            # Python 2
            self.slug = slugify(unicode(self.name))
        except NameError as e:
            # Python 3
            self.slug = slugify(str(self.name))
        super(MapGroup, self).save(*args, **kwargs)

        # Reset the stored image name
        self._original_image_name = self.image.name

    def _process_uploaded_image(self):
        """Handle image uploading.

        Images are all smartly resized to fit into the 345x194-hard-coded frame
        for list views.

        Also, all images are re-rendered as JPEG. This is done to keep size down
        as well as hopefully against any future attack vectors that might
        exploit rendering bugs in a client's image rendering library.

        If a transparent image (something with an alpha channel) is uploaded,
        the transparent areas will be replaced with solid white. This may be
        undesirable, so a future modification might need to turn this into a PNG
        so transparency is preserved.

        Doing the image processing is done inside the model rather than the form
        means that images uploaded in the django admin will also be properly
        resized.

        Bulk loads will skip processing (since they don't call the save method),
        but a bulk load will hopefully be accompanied by a bulk copy of the
        group images too.

        Uses the _original_image_name property to detect whether or not image
        processing should occur.

        Also, we try to be memory conservative by removing extra copies of
        images as soon as possible.
        """
        if self.image.name == self._original_image_name:
            # the image didn't change, so do nothing
            return

        # Delete the prior image if it exists.
        if self._original_image_name:
            self.image.storage.delete(self._original_image_name)

        # if there's no image, we're done.
        if not self.image.name:
            return

        # The image is different, so process the new one and delete the old
        # one.

        # Resize
        from PIL import Image, ImageColor, ImageOps
        from io import BytesIO

        uploaded_image = Image.open(self.image.file)

        # Fit image to size, centering in the middle width and top 2/5 height
        fit_uploaded_image = ImageOps.fit(uploaded_image, (345, 194),
                                          centering=(1 / 2., 2 / 5.))
        del uploaded_image

        # Account for images with transparency by rendering them on a white
        # background. Currently we're only producing JPEGs, but I suppose
        # we could use PNGs if preserving transparency becomes necessary.
        mask = None
        if fit_uploaded_image.mode == 'RGBA':
            mask = fit_uploaded_image

        group_image = Image.new('RGB', (345, 194), ImageColor.getrgb('white'))
        group_image.paste(fit_uploaded_image, mask=mask)
        group_image_data = BytesIO()
        group_image.save(group_image_data, 'JPEG')
        del group_image

        # Uploaded files come in (at least) two flavors:
        # InMemoryUploadedFile and TemporaryUploadedFile
        #
        # In order to save our modifications, we're just reaching in to the File
        #  data structure and altering it's. contents. Becaause of that, it
        # makes sense to be aware of the consequences.
        #
        # The file attribute is either a BytesIO or a NamedTemporaryFile.
        # Fortunately, both of these objects die gracefully; the BytesIO
        # will simply disappear, and the NamedTemporaryFile is only allowed
        # to exist while it's open. Thus, just dumping the existing file
        # will work to replace the image with the proper sized version of
        # itself.
        #
        # However, replacing the ImageField's File's file will break if
        # the internals are changed in some future django. For now, though,
        # I can't find an better way to alter the contents of the uploaded
        # file without writing it to disk first, and this works pretty well.

        group_image_data.seek(0)
        self.image.file.file = group_image_data


    def rename(self, new_name):
        """Rename the mapgroup and it's associated permission group.
        """
        self.name = new_name
        self.save()
        self.permission_group.name = self._permission_group_name()
        self.permission_group.save()

    def get_absolute_url(self):
        return reverse('mapgroups:detail', kwargs={'pk': self.pk,
                                                    'slug': self.slug})

    def has_member(self, user):
        """@type user User
        """
        if user.is_anonymous or not user.is_active:
            return False
        return self.mapgroupmember_set.filter(user=user).exists()

    def get_member(self, user):
        if user.is_anonymous or not user.is_active:
            return None
        try:
            return self.mapgroupmember_set.get(user=user)
        except MapGroupMember.DoesNotExist:
            return None

    def get_owner_membership(self):
        return self.owner.mapgroupmember_set.get(map_group_id=self.id)

    def _permission_group_name(self):
        """Compute the name of the permission group associated with this map
        group"""
        # The name is slug + 8 random chars
        # if the slug is >= 80 (Group.name max length), then replace the
        # last 8 chars with randomness.
        # This is done because slugs aren't guaranteed to be unique, but we
        # want permission groups to be unique to the map group.
        try:
            # Python 2
            name = slugify(unicode(self.name))
        except NameError as e:
            # Python 3
            name = slugify(str(self.name))
        name = name[:min(80 - 8, len(name))] + get_random_string(8)
        return name

    def image_url(self):
        if self.image:
            return self.image.url
        return static('mapgroups/mapgroups-default-image.jpg')


class MapGroupMember(models.Model):
    class Meta:
        unique_together = (('user', 'map_group',),)
        app_label = "mapgroups"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    map_group = models.ForeignKey(MapGroup, on_delete=models.CASCADE)

    date_joined = models.DateTimeField(auto_now_add=True)

    # permissions
    # is_owner = models.BooleanField(default=False, help_text=("If true, this "
    #                                "user is the group's creator."))
    is_manager = models.BooleanField(default=False, help_text=("If true, this "
                                     "user may perform admin actions on this "
                                     "group"))

    # user-group-specific preferences
    show_real_name = models.BooleanField(default=False)

    def __str__(self):
        return "%s's Membership card for %s" % (self.user.first_name, self.map_group.name)

    def user_name_for_group(self):
        """Return the user's name as it should appear in this group.
        """
        if self.show_real_name:
            return self.user.get_full_name()
        else:
            return self.user.get_short_name()

    def user_name_for_user(self, user):
        """Return the proper name to display to a specific user. If the member
        is not showing their real name, always display their Preferred Name.

        If both users are members of this group, show the member's
        real name. Otherwise show their preferred name.

        It might be a good idea to display the Real Name if the user's groups
        and member's groups overlap anywhere.
        """
        if not self.show_real_name:
            return self.user.get_short_name()

        if self.map_group.has_member(user):
            return self.user.get_full_name()
        else:
            return self.user.get_short_name()


class FeaturedGroupsManager(models.Manager):
    class Meta:
        app_label = "mapgroups"

    def get_queryset(self):
        return super(FeaturedGroupsManager, self).get_queryset().order_by('rank')


class FeaturedGroups(models.Model):
    class Meta:
        app_label = "mapgroups"

    rank = models.PositiveIntegerField(unique=True)
    # Note: unique FK here rather than 1:1, since the interface is a little
    # nicer in this case. You can say:
    # >>> mapgroup.featuredgroups_set.create(rank=4)
    # instead of:
    # >>> fg = FeaturedGroup.create(rank=4)
    # >>> mapgroup.featuredgroup = fg
    map_group = models.ForeignKey(MapGroup, unique=True, on_delete=models.CASCADE)

    def __str__(self):
        return "#%d %s" % (self.rank, self.map_group.name)


class RecentActivityManager(models.Manager):
    class Meta:
        app_label = "mapgroups"

    def get_queryset(self):
        qs = super(RecentActivityManager, self).get_queryset()
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        return qs.filter(date_created__gte=seven_days_ago)


# TODO: This isn't sufficient for admin messages
class ActivityLog(models.Model):
    """Record for events that have happened in this group.
    """
    class Meta:
        app_label = "mapgroups"

    group = models.ForeignKey(MapGroup, on_delete=models.CASCADE)
    message = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    admin = models.BooleanField(default=False, help_text=("If true, this"
                                " message is only viewable by managers."))
    associated_user = models.ForeignKey(User, null=True, blank=True,
                                        help_text=("The user this message is "
                                                   "associated with, if any."),
                                        on_delete=models.SET_NULL)

    recent = RecentActivityManager()
    objects = models.Manager()


class Invitation(models.Model):
    """A model to store user requests to join an invitation-only group, or
    admin invitations to a user.

    User selects "Join group"
    If that group is "open"
    """
    class Meta:
        app_label = "mapgroups"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(MapGroup, on_delete=models.CASCADE)
    message = models.CharField(max_length=512, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class EmailInvitation(models.Model):
    class Meta:
        app_label = "mapgroups"

    to_address = models.EmailField()
    map_group = models.ForeignKey(MapGroup, on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=32)
    invited_by = models.ForeignKey(MapGroupMember, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)
