import os

from rest_framework import permissions

from tenant_extras.utils import get_tenant_properties


def debug(message):
    if 'PERMISSIONS_DEBUG' in os.environ:
        print(message)


class BasePermission(permissions.BasePermission):
    """ BasePermission extends the standard BasePermission from DRF to include
    the ability to get the permissions without the request... Well ideally but
    currently the `view` is being passed which then gives access to the request
    TODO: it should be possible to get the permissions based on a `method`, `user`,
    and an optional `obj` which might be a parent type rather than the actual obj
    particularly if the permission being checked is the ability to create an obj

    """
    def has_object_permission(self, request, view, obj):
        """ This method is called from the views which include this permission.

        The call happens after the referenced obj has been fetched and will not be
        called if no object was found.

        Return `True` if permission is granted, `False` otherwise.
        """

        debug("BasePermission::{}::has_object_permission > {}".format(self.__class__.__name__, obj))
        if hasattr(obj, 'parent'):
            obj = obj.parent

        return self.has_object_method_permission(
            request.method, request.user, view, obj
        )

    def has_permission(self, request, view):
        """ This method is called from the views which include this permission.

        The call happens during view initalisation so it will be called with views returning
        a data set as well as a single object.

        Return `True` if permission is granted, `False` otherwise.
        """
        debug("BasePermission::{}::has_permission > {}".format(self.__class__.__name__, view))
        return self.has_method_permission(
            request.method, request.user, view
        )

    def has_object_method_permission(self, method, user, view, obj):
        """ Check if user has permission to access method on obj for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """
        message = 'has_object_method_permission() must be implemented on {}'.format(self)
        raise NotImplementedError(message)

    def has_method_permission(self, method, user, view, obj=None):
        """ Check if user has permission to access method for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """
        message = 'has_method_permission() must be implemented on {}'.format(self)
        raise NotImplementedError(message)


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

    def has_method_permission(self, method, user, view, obj=None):
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
        debug("ResourcePermissions::has_method_permission > {}".format(user.has_perms(perms)))
        return user.has_perms(perms)

    def has_object_method_permission(self, method, user, view, obj=None):
        debug("ResourcePermissions::has_object_method_permission > {}".format(self.has_method_permission(method, user,
                                                                              view)))
        return self.has_method_permission(method, user, view)


class OwnerPermission(BasePermission):
    """
    Allows access only to obj owner.
    """

    def has_object_method_permission(self, method, user, view, obj):
        debug("OwnerPermission::has_object_permission > {}".format(user == obj.owner))
        return user == obj.owner

    def has_method_permission(self, method, user, view):
        return True


class OwnerOrAdminPermission(OwnerPermission):
    def check_permission(self, request, instance):
        pass

    def has_object_method_permission(self, method, user, view, obj):
        debug("IsOwnerOrAdmin::has_object_method_permission > {}".format(user == obj.owner or user.is_staff))
        return user == obj.owner or user.is_staff


class RelatedResourceOwnerPermission(BasePermission):
    parent_class = None

    def get_parent_from_request(self, request):
        """ For requests to list endpoints, eg when creating an object then
        get_parent needs to be defined to use this permission class.
        """
        raise NotImplementedError('get_parent_from_request() must be implemented')

    def has_object_method_permission(self, method, user, view, obj):
        debug("OwnerPermission::has_object_permission > {}".format(user == obj.owner))
        return user == obj.owner

    def has_method_permission(self, method, user, view):
        """ Read permissions are allowed to any request, so we'll< always allow
        GET, HEAD or OPTIONS requests.
        """
        if method != 'POST':
            debug("OwnerPermission::has_method_permission > {}".format(True))
            return True

        parent = self.get_parent_from_request(view.request)
        debug("OwnerPermission::has_method_permission > {}".format(user == parent.owner))
        return user == parent.owner


class UserPermission(BasePermission):
    pass


class TenantConditionalOpenClose(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_object_method_permission(self, method, user, view, obj):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True

    def has_method_permission(self, method, user, view, obj=None):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True
