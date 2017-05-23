from rest_framework import permissions


class NoDonationsOrReadOnly(permissions.BasePermission):
    """
    If a reward has no donations it should be editable/deletable
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return not obj.count
