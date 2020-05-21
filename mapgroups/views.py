from django.contrib.auth.decorators import login_required
try:
    from django.urls import reverse, reverse_lazy
except ModuleNotFoundError:
    from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View, FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, ModelFormMixin
from django.views.generic.list import ListView

from mapgroups.actions import join_map_group, leave_non_owned_map_group, \
    delete_owned_map_group
from mapgroups.forms import CreateGroupForm, JoinMapGroupActionForm, \
    RequestJoinMapGroupActionForm, EditMapGroupForm, MapGroupPreferencesForm, \
    LeaveMapGroupActionForm, DeleteMapGroupActionForm, RemoveMapGroupImageForm
from mapgroups.models import MapGroup, FeaturedGroups
from nursery.view_helpers import decorate_view


@decorate_view(login_required)
class MapGroupCreate(FormView):
    form_class = CreateGroupForm
    template_name = 'mapgroups/mapgroup_form.html'

    def form_valid(self, form):
        image = form.files.get('image', '')
        mg, member = MapGroup.objects.create(name=form.cleaned_data['name'],
                                             blurb=form.cleaned_data['blurb'],
                                             open=form.cleaned_data['is_open'],
                                             owner=self.request.user,
                                             image=image)
        self.object = mg

        kwargs = {
            'pk': mg.id,
            'slug': mg.slug,
        }

        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)

        return super(MapGroupCreate, self).form_valid(form)

    def form_invalid(self, form):
        return super(MapGroupCreate, self).form_invalid(form)

    def get(self, request, *args, **kwargs):
        return super(MapGroupCreate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(MapGroupCreate, self).post(request, *args, **kwargs)

class MapGroupDetailView(DetailView):
    model = MapGroup
    context_object_name ='mapgroup'

    def get_context_data(self, **kwargs):
        context = super(MapGroupDetailView, self).get_context_data(**kwargs)
        context['title'] = self.object.name
        context['owner'] = self.object.get_owner_membership()
        context['user_is_member'] = self.object.has_member(self.request.user)
        context['membership'] = self.object.get_member(self.request.user)
        if context['membership']:
            show_real_name = context['membership'].show_real_name
        else:
            show_real_name = None

        context['preferences_form'] = MapGroupPreferencesForm({
            'show_real_name': show_real_name
        })

        pg = self.object.permission_group
        shared_items = {}
        shared_items['bookmarks'] = pg.visualize_bookmark_related.all()
        shared_items['scenarios'] = pg.scenarios_scenario_related.all()
        shared_items['leaseblock_selections'] = pg.scenarios_leaseblockselection_related.all()
        shared_items['drawings'] = pg.drawing_aoi_related.all()
        shared_items['windenergysites'] = pg.drawing_windenergysite_related.all()

        if any(shared_items.values()):
            context['shared_items'] = shared_items

        members = self.object.mapgroupmember_set.exclude(user=self.object.owner)
        members = list(members)
        members.sort(key=lambda x: x.user_name_for_user(self.request.user).lower())
        members.insert(0, self.object.get_owner_membership())
        context['sorted_member_list'] = members

        return context

class MapGroupListView(ListView):
    model = MapGroup

    def get_context_data(self, **kwargs):
        context = super(MapGroupListView, self).get_context_data(**kwargs)
        context['featured_mapgroups'] = FeaturedGroups.objects.all()
        context['mapgroups'] = MapGroup.not_featured.all()
        return context


@decorate_view(login_required)
class JoinMapGroupActionView(FormView):
    """FormView to join a map group.
    It has a slightly modified flow, since there are, in fact, no form fields.
    After get/post, the user is merely redirected to the appropriate url.
    """
    template_name = None
    form_class = JoinMapGroupActionForm

    def handle(self, request, *args, **kwargs):
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)

        member = join_map_group(self.request.user, self.mapgroup)
        if not member:
            # then it's a closed group and we need an invite
            pass

        return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        """Get needed to allow non-logged in users to join a group immediately
        after login.
        """
        return self.handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)


@decorate_view(login_required)
class LeaveMapGroupActionView(FormView):
    template_name = None
    form_class = LeaveMapGroupActionForm

    def post(self, request, *args, **kwargs):
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)
        return super(LeaveMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = leave_non_owned_map_group(self.request.user, self.mapgroup)
        if not success:
            # Then we weren't able to leave the group, probably because we
            # own it or are a member
            pass

        return super(LeaveMapGroupActionView, self).form_valid(form)


@decorate_view(login_required)
class DeleteMapGroupActionView(FormView):
    template_name = None
    form_class = DeleteMapGroupActionForm

    def post(self, request, *args, **kwargs):
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.success_url = reverse('mapgroups:list')
        return super(DeleteMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = delete_owned_map_group(self.request.user, self.mapgroup)
        if not success:
            # Then we weren't able to delete the group, probably because we
            # don't own it
            pass

        return super(DeleteMapGroupActionView, self).form_valid(form)


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


@decorate_view(login_required)
class MapGroupEditView(FormView):
    template_name = 'mapgroups/mapgroup_edit.html'
    form_class = EditMapGroupForm

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)

        return {
            'name': mg.name,
            'blurb': mg.blurb,
            'is_open': mg.is_open,
        }

    def get_context_data(self, **kwargs):
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        kwargs.update({'mapgroup': mg})
        return kwargs

    def get(self, request, *args, **kwargs):
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        return super(MapGroupEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        return super(MapGroupEditView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        self.success_url = mg.get_absolute_url()

        mg.blurb = form.cleaned_data['blurb']
        mg.is_open = form.cleaned_data['is_open']

        # If the user didn't upload a new image, leave the old one alone.
        if form.cleaned_data['image']:
            mg.image = form.cleaned_data['image']

        mg.save()

        mg.rename(form.cleaned_data['name'])

        return super(FormView, self).form_valid(form)

@decorate_view(login_required)
class RemoveMapGroupImageActionView(FormView):
    template_name = None
    form_class = RemoveMapGroupImageForm

    def post(self, request, *args, **kwargs):
        self.mapgroup = get_object_or_404(MapGroup, pk=kwargs['pk'], owner=request.user)
        self.success_url = reverse('mapgroups:edit', kwargs=kwargs)
        return super(RemoveMapGroupImageActionView, self).post(request, *args,
                                                               **kwargs)

    def form_valid(self, form):
        self.mapgroup.image = ''
        self.mapgroup.save()

        return super(RemoveMapGroupImageActionView, self).form_valid(form)


@decorate_view(login_required)
class MapGroupPreferencesView(FormView):
    template_name = None
    form_class = MapGroupPreferencesForm

    def post(self, request, *args, **kwargs):
        # can't define the success_url on the class, since we don't know which
        # mapgroup it is until the post
        self.mapgroup = MapGroup.objects.get(pk=kwargs['pk'])
        self.member = self.mapgroup.get_member(self.request.user)
        if not self.member:
            return HttpResponseNotFound()

        self.success_url = reverse('mapgroups:detail', kwargs=kwargs)
        return super(MapGroupPreferencesView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.member.show_real_name = form.cleaned_data['show_real_name']
        self.member.save()

        return super(MapGroupPreferencesView, self).form_valid(form)
