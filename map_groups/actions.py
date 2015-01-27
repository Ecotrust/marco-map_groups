from map_groups.models import MapGroup, MapGroupMember


def add_user_to_group():
    pass


def create_map_group(owner):
    """Creates a new map group with the specified options.
    """

    mg = MapGroup()
    mg.name

    member = MapGroupMember()
    member.is_owner = True
    member.is_manager = True
    member.user = owner
    member.map_group = mg
    member.save()

