from rest_framework.permissions import BasePermission

OWNER_FIELD = "user"


class IsWorkspaceOwner(BasePermission):
    """Object-level guard: only the owner may touch a workspace.

    The viewset queryset is already scoped to the user; this is defence in depth."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, f"{OWNER_FIELD}_id") == request.user.id
