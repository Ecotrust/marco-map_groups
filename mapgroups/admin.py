from django.contrib import admin
from mapgroups.models import MapGroup, FeaturedGroups, MapGroupMember


class FeaturedMapGroupAdmin(admin.StackedInline):
    model = FeaturedGroups
    extra = 1

class MapGroupMemberAdmin(admin.StackedInline):
    model = MapGroupMember
    extra = 1

class MapGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

    inlines = [FeaturedMapGroupAdmin, MapGroupMemberAdmin]

    def has_add_permission(self, request):
        """Restrict creating new map groups in admin
        """
        return False

    def delete_queryset(self, request, object):
        pgroups = []
        for mgroup in object:
            pgroup = mgroup.permission_group
            pgroups.append(pgroup)
        object.delete()
        for pgroup in pgroups:
            pgroup.delete()

admin.site.register(MapGroup, MapGroupAdmin)
