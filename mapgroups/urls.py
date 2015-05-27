"""
Experimental URL patterns module.
SRH Jan-2015

For 3rd party modules, I'd like the including project to be able to specify a
namespace for URL names. At the same time, in the module, I'd like to be able
to reverse URLs in views, tests, and models without knowledge of what namespace
the project is using.

The app_name and namespaces are defined external to the module, which seems to
be a design flaw (or maybe I'm interpreting what the design is supposed to do
incorrectly).

The best solution seems to be to provide a 'urls()' function which is called
to get the module's URLs. It sets the app_name to a known value (for use
internally by the module), and namespace to the value provided by the project,
for use in the project's code. (I think app_name should be the name of the
module providing the URLs, but that is not easy to auto-discover, especially if
the URLs are generated).

Short version:
Usage:

    import map_groups.urls
    urls(r'^mount_point/', include(map_groups.urls.urls('Project Name Space'))
"""

from django.conf.urls import url, include
from mapgroups import rpc
from mapgroups.views import MapGroupDetailView, \
    MapGroupCreate, MapGroupListView, JoinMapGroupActionView, \
    RequestJoinMapGroupActionView, MapGroupEditView, MapGroupPreferencesView, \
    LeaveMapGroupActionView, DeleteMapGroupActionView, \
    RemoveMapGroupImageActionView

_urlpatterns = [
    # Map group urls look something like:
    #   midatlanticoceans.org/g/49/swiftly-sinking-sailfish
    # but
    #   midatlanticoceans.org/g/49
    # will also work

    url(r'^$', MapGroupListView.as_view(), name='list'),
    url(r'^create$', MapGroupCreate.as_view(), name='create'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/edit$',
        MapGroupEditView.as_view(), name='edit'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/edit/remove-image$',
        RemoveMapGroupImageActionView.as_view(), name='remove-image'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/$',
        MapGroupDetailView.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/preferences$',
        MapGroupPreferencesView.as_view(), name='preferences'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/join$',
        JoinMapGroupActionView.as_view(), name='join'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/leave$',
        LeaveMapGroupActionView.as_view(), name='leave'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/delete$',
        DeleteMapGroupActionView.as_view(), name='delete'),
    url(r'^(?P<pk>\d+)/(?P<slug>[\w-]+)/join$',
        RequestJoinMapGroupActionView.as_view(), name='request-join'),
]

def urls(namespace='mapgroups'):
    """Returns a 3-tuple for use with include().

    The including module or project can refer to urls as namespace:urlname,
    internally, they are referred to as app_name:urlname.
    """
    return (_urlpatterns, 'mapgroups', namespace)

