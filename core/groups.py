from django.contrib.auth.models import Group

def add_user_to_group(user, group_name:str) -> None:
    group, _ = Group.objects.get_or_create(name=group_name)

    if not user.groups.filter(id=group.id).exists():
        user.groups.add(group)
    

def remove_user_to_group(user, group_name:str) -> None:
    group = Group.objects.filter(name=group_name).first()

    if group and user.groups.filter(id=group.id).exists():
        user.groups.remove(group)

def clear_user_groups(user) -> None:
    user.groups.clear()