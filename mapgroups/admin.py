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

    def has_delete_permission(self, request, obj=None):
        """Restrict deleting map groups in admin
        """
        return False

admin.site.register(MapGroup, MapGroupAdmin)
