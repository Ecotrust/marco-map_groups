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

admin.site.register(MapGroup, MapGroupAdmin)
