from rest_framework import permissions


class IsConnectedToProfile(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user has the Place set in their profile
        """
        return (
            obj.member_set.filter(id=request.user.id).exists()
            or request.user.is_superuser
            or request.user.is_staff
        )
