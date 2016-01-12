from rest_framework import permissions


class NoDonationsOrReadOnly(permissions.BasePermission):
    """
    If a reward has doantions it should be editable
    """
    def has_object_permission(self, request, view, obj):
        return not obj.count