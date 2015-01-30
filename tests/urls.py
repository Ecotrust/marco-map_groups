from django.conf.urls import url, include
import mapgroups.urls

urlpatterns = [
    url(r'^g/', include(mapgroups.urls.urls())),
]
