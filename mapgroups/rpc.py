"""
Placeholder file for a future JSON-RPC endpoint in mapgroups.
For now, contains views that return JsonResponses.

SRH Feb-2015
"""
from django.conf.urls import url, include
from django.http import JsonResponse

urls = []

def set_url(pattern):
    def pass_through(f):
        urls.append(url(pattern, f, name=f.__name__))
        return f
    return pass_through

@set_url(r'^get_sharing_groups$')
def get_sharing_groups(request):
    # locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    # data = []
    # sharing_groups = user_sharing_groups(request.user)
    # for group in sharing_groups:
    #     members = []
    #     for user in group.user_set.all():
    #         members.append(user.get_short_name())
    #     sorted_members = sorted(members, key=cmp_to_key(locale.strcoll))
    #     data.append({
    #         'group_name': group.name,
    #         'group_slug': slugify(group.name)+'-sharing',
    #         'members': sorted_members
    #     })
    # return HttpResponse(json.dumps(data))

    data = []
    if not request.user.is_anonymous():
        for membership in request.user.mapgroupmember_set.all():
            group = membership.map_group
            members = [member.user_name_for_group()
                       for member in group.mapgroupmember_set.all()]
            members.sort()

            data.append({
                'group_name': group.name,
                'group_slug': group.permission_group_name(),
                'members': members,
            })

    # safe=False because it's a list.
    # TODO: refactor into a dict response,
    # i.e., {group_name: {slug: ..., members: [...]}}
    return JsonResponse(data, safe=False)

