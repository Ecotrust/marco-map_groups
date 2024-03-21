from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, BooleanField
try:
    from django.urls import reverse, reverse_lazy
except (ModuleNotFoundError, ImportError):
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
    delete_owned_map_group, update_map_group_membership_status, \
    update_map_group_membership_manager
from mapgroups.forms import CreateGroupForm, JoinMapGroupActionForm, \
    RequestJoinMapGroupActionForm, EditMapGroupForm, MapGroupPreferencesForm, \
    LeaveMapGroupActionForm, DeleteMapGroupActionForm, RemoveMapGroupImageForm, \
    ApproveMapGroupActionForm, DenyMapGroupActionForm, \
    PromoteMapGroupMemberActionForm, RemoveMapGroupMemberActionForm
from mapgroups.models import MapGroup, FeaturedGroups, MapGroupMember
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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(request, object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, request, **kwargs):
        context = super(MapGroupDetailView, self).get_context_data(**kwargs)
        context['title'] = self.object.name
        context['owner'] = self.object.get_owner_membership()
        context['user_is_member'] = self.object.has_member(self.request.user)
        membership = self.object.get_member(self.request.user)
        context['membership'] = membership
        if membership:
            show_real_name = membership.show_real_name
            context['user_is_manager'] = membership.is_manager
        else:
            show_real_name = None
            context['user_is_manager'] = False


        context['preferences_form'] = MapGroupPreferencesForm({
            'show_real_name': show_real_name
        })

        pg = self.object.permission_group
        shared_items = {}
        shared_items['bookmarks'] = pg.visualize_bookmark_related.all().annotate(
            is_owner=Case(
                When(
                    user=request.user, then=True
                ), 
                default=False, 
                output_field=BooleanField()
            )
        ).order_by('-is_owner','name','user')
        shared_items['scenarios'] = pg.scenarios_scenario_related.all().annotate(is_owner=Case(When(user=request.user, then=True), default=False, output_field=BooleanField())).order_by('-is_owner','name','user')
        shared_items['leaseblock_selections'] = pg.scenarios_leaseblockselection_related.all().annotate(is_owner=Case(When(user=request.user, then=True), default=False, output_field=BooleanField())).order_by('-is_owner','name','user')
        shared_items['drawings'] = pg.drawing_aoi_related.all().annotate(is_owner=Case(When(user=request.user, then=True), default=False, output_field=BooleanField())).order_by('-is_owner','name','user')
        shared_items['windenergysites'] = pg.drawing_windenergysite_related.all().annotate(is_owner=Case(When(user=request.user, then=True), default=False, output_field=BooleanField())).order_by('-is_owner','name','user')
        shared_items['user_imported_layers'] = pg.visualize_userlayer_related.all().annotate(is_owner=Case(When(user=request.user, then=True), default=False, output_field=BooleanField())).order_by('-is_owner','name','user')

        if any(shared_items.values()):
            context['shared_items'] = shared_items

        members = self.object.mapgroupmember_set.exclude(user=self.object.owner)
        confirmed_members = members.filter(status='Accepted')
        confirmed_members = list(confirmed_members)
        confirmed_members.sort(key=lambda x: x.user_name_for_user(self.request.user).lower())
        confirmed_members.insert(0, self.object.get_owner_membership())
        context['sorted_member_list'] = confirmed_members

        member_requests = members.filter(status='Pending')
        member_requests = list(member_requests)
        member_requests.sort(key=lambda x: x.user_name_for_user(self.request.user).lower())
        context['member_requests'] = member_requests

        split_string = '9999LKSEJF09999'    #sufficiently complex to be unlikely to occur natually, but even that is handled below
        context['drawing_admin_root_url'] = split_string.join(reverse('admin:drawing_aoi_change', args=(split_string,)).split(split_string)[0:-1])
        context['user_admin_root_url'] = split_string.join(reverse('admin:auth_user_change', args=(split_string,)).split(split_string)[0:-1])
        context['user_layer_admin_root_url'] = split_string.join(reverse('admin:visualize_userlayer_change', args=(split_string,)).split(split_string)[0:-1])


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
class ApproveMapGroupActionView(FormView):
    template_name = None
    form_class = ApproveMapGroupActionForm

    def post(self, request, *args, **kwargs):
        self.membership = MapGroupMember.objects.get(pk=kwargs['pk'])
        detail_kwargs = {
            'pk': self.membership.map_group.pk,
            'slug': self.membership.map_group.slug
        }
        self.success_url = reverse('mapgroups:detail', kwargs=detail_kwargs)
        return super(ApproveMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = update_map_group_membership_status(self.request.user, self.membership, 'Accepted')
        if not success:
            # User is not permitted to manage this group membership request
            pass

        return super(ApproveMapGroupActionView, self).form_valid(form)

@decorate_view(login_required)
class DenyMapGroupActionView(FormView):
    template_name = None
    form_class = ApproveMapGroupActionForm

    def post(self, request, *args, **kwargs):
        self.membership = MapGroupMember.objects.get(pk=kwargs['pk'])
        detail_kwargs = {
            'pk': self.membership.map_group.pk,
            'slug': self.membership.map_group.slug
        }
        self.success_url = reverse('mapgroups:detail', kwargs=detail_kwargs)
        return super(DenyMapGroupActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = update_map_group_membership_status(self.request.user, self.membership, 'Rejected')
        if not success:
            # User is not permitted to manage this group membership request
            pass

        return super(DenyMapGroupActionView, self).form_valid(form)

@decorate_view(login_required)
class PromoteMapGroupMemberActionView(FormView):
    template_name = None
    form_class = PromoteMapGroupMemberActionForm

    def post(self, request, *args, **kwargs):
        self.membership = MapGroupMember.objects.get(pk=kwargs['pk'])
        detail_kwargs = {
            'pk': self.membership.map_group.pk,
            'slug': self.membership.map_group.slug
        }
        self.success_url = reverse('mapgroups:detail', kwargs=detail_kwargs)
        return super(PromoteMapGroupMemberActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = update_map_group_membership_manager(self.request.user, self.membership, True)
        if not success:
            # User is not permitted to manage this group membership request
            pass

        return super(PromoteMapGroupMemberActionView, self).form_valid(form)

@decorate_view(login_required)
class DemoteMapGroupMemberActionView(FormView):
    template_name = None
    form_class = PromoteMapGroupMemberActionForm

    def post(self, request, *args, **kwargs):
        self.membership = MapGroupMember.objects.get(pk=kwargs['pk'])
        detail_kwargs = {
            'pk': self.membership.map_group.pk,
            'slug': self.membership.map_group.slug
        }
        self.success_url = reverse('mapgroups:detail', kwargs=detail_kwargs)
        return super(DemoteMapGroupMemberActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        success = update_map_group_membership_manager(self.request.user, self.membership, False)
        if not success:
            # User is not permitted to manage this group membership request
            pass

        return super(DemoteMapGroupMemberActionView, self).form_valid(form)

@decorate_view(login_required)
class RemoveMapGroupMemberActionView(FormView):
    template_name = None
    form_class = RemoveMapGroupMemberActionForm

    def post(self, request, *args, **kwargs):
        self.membership = MapGroupMember.objects.get(pk=kwargs['pk'])
        detail_kwargs = {
            'pk': self.membership.map_group.pk,
            'slug': self.membership.map_group.slug
        }
        self.success_url = reverse('mapgroups:detail', kwargs=detail_kwargs)
        return super(RemoveMapGroupMemberActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        if self.membership.is_manager:
            update_map_group_membership_manager(self.request.user, self.membership, False)
        success = update_map_group_membership_status(self.request.user, self.membership, 'Rejected')
        if not success:
            # User is not permitted to manage this group membership request
            pass

        return super(RemoveMapGroupMemberActionView, self).form_valid(form)

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
    form_class = EditMapGroupForm
    template_name = 'mapgroups/mapgroup_edit.html'
    model = MapGroup
    success_url = '.'

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        return {
            'name': mg.name,
            'blurb': mg.blurb,
            'is_open': mg.is_open,
            'image': mg.image,
        }

    def get_context_data(self, **kwargs):
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        context = super(MapGroupEditView, self).get_context_data(**kwargs)
        context.update({'mapgroup': mg})
        return context

    def get(self, request, *args, **kwargs):
        # mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        return super(MapGroupEditView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super(MapGroupEditView, self).get_form_kwargs()
        mg = get_object_or_404(MapGroup, owner=self.request.user, **self.kwargs)
        if mg:
            form_kwargs['initial']['name'] = mg.name
            form_kwargs['initial']['blurb'] = mg.blurb
            form_kwargs['initial']['is_open'] = mg.is_open
            form_kwargs['initial']['image'] = mg.image

        return form_kwargs

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
