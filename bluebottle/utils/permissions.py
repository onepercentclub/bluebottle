import os

from rest_framework import permissions

from tenant_extras.utils import get_tenant_properties


def debug(message):
    if 'PERMISSIONS_DEBUG' in os.environ:
        print(message)


class ResourcePermissions(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class ResourceOwnerPermission(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.api_read_own_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_own_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_own_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_own_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class OwnerPermission():
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


class RelatedResourceOwnerPermission():
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


class UserPermission():
    pass

class IsAuthenticated():
    pass


class TenantConditionalOpenClose():
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return request.user and request.user.is_authenticated()
        except AttributeError:
            pass
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True
