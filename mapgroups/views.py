from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import View, FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, ModelFormMixin
from django.views.generic.list import ListView

from mapgroups.actions import create_map_group, join_map_group
from mapgroups.forms import CreateGroupForm, JoinMapGroupActionForm, \
    RequestJoinMapGroupActionForm
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
    fields = ['name', 'blurb', 'is_open']

    def form_valid(self, form):
        mg, member = create_map_group(name=form.cleaned_data['name'],
                                      blurb=form.cleaned_data['blurb'],
                                      open=form.cleaned_data['is_open'],
                                      owner=self.request.user)
        self.object = mg
        return super(ModelFormMixin, self).form_valid(form)


class MapGroupDetailView(DetailView):
    model = MapGroup
    context_object_name ='mapgroup'

    def get_context_data(self, **kwargs):
        context = super(MapGroupDetailView, self).get_context_data(**kwargs)
        context['title'] = self.object.name

        context['user_is_member'] = self.object.has_member(self.request.user)
        return context


class MapGroupListView(ListView):
    model = MapGroup
    context_object_name ='mapgroups'


@decorate_view(login_required)
class JoinMapGroupActionView(FormView):
    template_name = None
    form_class = JoinMapGroupActionForm

    def post(self, request, *args, **kwargs):
        # can't define the success_url on the class, since we don't know which
        # mapgroup it is until the post
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)
        return super(JoinMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        member = join_map_group(self.request.user, self.mapgroup)
        if not member:
            # then it's a closed group and we need an invite
            pass

        return super(JoinMapGroupActionView, self).form_valid(form)

@decorate_view(login_required)
class RequestJoinMapGroupActionView(FormView):
    """Process a join request for a closed group.
    """
    template_name = None
    form_class = RequestJoinMapGroupActionForm

    def post(self, request, *args, **kwargs):
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)
        return super(RequestJoinMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        member = join_map_group(self.request.user, self.mapgroup)
        if not member:
            # then it's a closed group and we need an invite
            pass

        return super(RequestJoinMapGroupActionView, self).form_valid(form)
