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


class OwnerOrCreate(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user has the Place set in their profile
        """
        return (
            not obj.member_set.exists()
            or obj.member_set.filter(id=request.user.id).exists()
            or request.user.is_superuser
            or request.user.is_staff
        )
