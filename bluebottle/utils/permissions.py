import logging

from rest_framework import permissions

from tenant_extras.utils import get_tenant_properties

logger = logging.getLogger(__name__)


class PermissionsException(Exception):
    pass


class BasePermission(permissions.BasePermission):
    """ BasePermission extends the standard BasePermission from DRF to include
    the ability to get the permissions without the request.

    Currently the `view` is being passed which then gives access to the request.

    TODO: it should be possible to get the permissions based on a `action`, `user`,
    and an optional `obj` which might be a parent type rather than the actual obj
    particularly if the permission being checked is the ability to create an obj

    """

    def get_view_model(self, view):
        model_cls = None
        try:
            model_cls = view.model
        except AttributeError:
            message = (
                'The related view `{}` does not have a model property.'.format(view.__class__.__name__),
                'Is this a legacy view using ResourcePermissions?'
            )
            raise PermissionsException(' '.join(message))

        return model_cls

    def has_object_permission(self, request, view, obj):
        """ This action is called from the views which include this permission.

        The call happens after the referenced obj has been fetched and will not be
        called if no object was found.

        Return `True` if permission is granted, `False` otherwise.
        """

        return self.has_object_action_permission(
            request.method, request.user, obj
        )

    def has_permission(self, request, view):
        """ This action is called from the views which include this permission.

        The call happens during view initalisation so it will be called with views returning
        a data set as well as a single object.

        Return `True` if permission is granted, `False` otherwise.
        """

        try:
            model_cls = self.get_view_model(view)
            return self.has_action_permission(
                request.method, request.user, model_cls
            )
        except TypeError as err:
            message = (
                '{} not implemented correctly.'.format(self.__class__.__name__),
                'Error: {}'.format(err.message)
            )
            raise PermissionsException(' '.join(message))
        except PermissionsException:
            return super(BasePermission, self).has_permission(request, view)

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        """ Check if user has permission to access action on obj for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """

        message = 'has_object_action_permission() must be implemented on {}'.format(self)
        raise NotImplementedError(message)

    def has_action_permission(self, action, user, model_cls):
        """ Check if user has permission to access action for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """

        message = 'has_action_permission() must be implemented on {}'.format(self)
        raise NotImplementedError(message)


class ResourcePermission(BasePermission, permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_%(model_name)s'],
    }

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        return True

    def has_action_permission(self, action, user, model_cls):
        perms = self.get_required_permissions(action, model_cls)
        return user.has_perms(perms)


class ResourceOwnerPermission(ResourcePermission):
    """ Allows access only to obj owner. """
    perms_map = {
        'GET': ['%(app_label)s.api_read_own_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_own_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_own_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_own_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_own_%(model_name)s'],
    }

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        return user == obj.owner


class RelatedResourceOwnerPermission(ResourceOwnerPermission):
    """ Allows access only to obj owner of related resource.

    This class assumes the child resource has a `parent` property which will return the parent object.
    """
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return user == parent.owner


class OwnerOrParentOwnerOrAdminPermission(RelatedResourceOwnerPermission):
    """ Allows access only to obj owner, parent owner and admin users. """

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return getattr(obj, 'owner') == user or getattr(parent, 'owner') == user


class TenantConditionalOpenClose(BasePermission):
    """ Allows access only to authenticated users. """

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True

    def has_action_permission(self, action, user, model_cls):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True


class IsAuthenticated(BasePermission):
    """ Allow access if the user is authenticated. """

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        return self.has_action_permission(action, user, None)

    def has_action_permission(self, action, user, model_cls):
        return user and user.is_authenticated


class AuthenticatedOrReadOnlyPermission(IsAuthenticated):
    """ Allow access if the user is authenticated or the request uses a safe action. """

    def has_action_permission(self, action, user, model_cls):
        if action in permissions.SAFE_METHODS:
            return True
        return user and user.is_authenticated


def OneOf(*permission_classes):
    class OneOf(BasePermission):
        permissions = permission_classes

        def has_object_permission(self, request, view, obj):
            action = request.method
            user = request.user
            return any(
                (
                    perm().has_object_action_permission(action, user, obj) and
                    perm().has_action_permission(action, user, view.model)
                ) for perm in self.permissions
            )

        def has_object_action_permission(self, *args, **kwargs):
            return any(
                perm().has_object_action_permission(*args, **kwargs) for
                perm in self.permissions
            )

        def has_action_permission(self, *args, **kwargs):
            return any(
                perm().has_action_permission(*args, **kwargs) for
                perm in self.permissions
            )

    return OneOf
