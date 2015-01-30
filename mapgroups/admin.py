from django.contrib import admin
from mapgroups.models import MapGroup


class MapGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(MapGroup, MapGroupAdmin)
