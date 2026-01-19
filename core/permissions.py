from rest_framework.permissions import BasePermission

class HasPerm(BasePermission):
    def __init__(self, perm: str):
        self.perm = perm

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.has_perm(self.perm))