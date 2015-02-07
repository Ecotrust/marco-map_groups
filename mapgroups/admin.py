from django.contrib import admin
from mapgroups.models import MapGroup, FeaturedGroups


class FeaturedMapGroupAdmin(admin.StackedInline):
    model = FeaturedGroups


class MapGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

    inlines = [FeaturedMapGroupAdmin]

admin.site.register(MapGroup, MapGroupAdmin)
