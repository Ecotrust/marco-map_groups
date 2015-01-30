from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, ModelFormMixin
from django.views.generic.list import ListView

from mapgroups.actions import create_map_group
from mapgroups.forms import CreateGroupForm
from mapgroups.models import MapGroup

def decorate_view(fn):
    """Decorate a django view class with the specified view decorator.

    For example,
        @decorate_view(login_required)
        class SomeView(View):
            pass

    Django's prescribed method of creating a MixIn class doesn't seem to work
    100% of the time, particularly with generic views.
    (https://docs.djangoproject.com/en/1.7/topics/class-based-views/intro/#decorating-the-class)
    """

    def require(cls):
        cls.dispatch = method_decorator(fn)(cls.dispatch)
        return cls
    return require


@decorate_view(login_required)
class MapGroupCreate(CreateView):
    model = MapGroup
    fields = ['name', 'blurb']

    def form_valid(self, form):
        mg, member = create_map_group(name=form.cleaned_data['name'],
                                      blurb=form.cleaned_data['blurb'],
                                      owner=self.request.user)
        self.object = mg
        return super(ModelFormMixin, self).form_valid(form)


class MapGroupDetailView(DetailView):
    model = MapGroup
    context_object_name ='mapgroup'

    def get_context_data(self, **kwargs):
        context = super(MapGroupDetailView, self).get_context_data(**kwargs)
        context['title'] = self.object.name
        return context


class MapGroupListView(ListView):
    model = MapGroup
    context_object_name ='mapgroups'


