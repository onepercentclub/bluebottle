from rest_framework import permissions


class BasePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'parent'):
            obj = parent

        return self.check_object_permission(
            request.method, request.user, view, obj
        )

    def has_permission(self, request, view):
        return self.check_permission(
            request.method, request.user, view
        )

    def check_object_permission(self, method, user, view, obj):
        """ Check if user has permission to acces method on obj for the view view

        Used by both the DRF permission system and voor returning permissions to the user
        """
        raise NotImplemented()

    def check_permission(self, method, user, view, obj):
        """ Check if user has permission to acces method for the view view

        Used by both the DRF permission system and voor returning permissions to the user
        """
        raise NotImplemented()


class IsUser(permissions.BasePermission):
    pass


class IsOwner(permissions.BasePermission):
    """
    Allows access only to obj owner.
    """

    owner_field = 'owner'

    def get_owner(self, obj):
        return getattr(obj, self.owner_field, None)

    def check_object_permission(self, method, user, view, obj):
        return user == self.get_owner(obj)

    def check_permission(self, method, user, view, obj):
        return self.check_permission(method, user, view)


class ResourcePermissions(BasePermission, permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_%(model_name)s'],
    }

    def check_permission(self, method, user, view):
        queryset = None
        if hasattr(view, 'queryset'):
            queryset = view.queryset
        elif hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()

        assert queryset is not None, (
            'Cannot apply DjangoModelPermissions on a view that '
            'does not set `.queryset` or have a `.get_queryset()` method.'
        )

        perms = self.get_required_permissions(method, queryset.model)

        return user.has_perms(perms)

    def check_object_permission(self, method, user, view, obj):
        return self.check_permission(method, user, view)
