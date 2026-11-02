from rest_framework.permissions import BasePermission


class IsWorkspaceOwner(BasePermission):
    """Object-level guard: only the owner may touch a workspace."""
    
    @property
    def owner_field(self):
        return "user"

    def has_object_permission(self, request, view, obj):
        return getattr(obj, self.owner_field) == request.user


