from rest_framework import permissions

from tenant_extras.utils import get_tenant_properties


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

        model_cls = None
        try:
            model_cls = view.model
        except AttributeError:
            message = (
                'The related view `{}` does not have a model property.'.format(view.__class__.__name__),
                'Is this a legacy view using ResourcePermissions?'
            )
            raise PermissionsException(' '.join(message))

        return self.has_action_permission(
            request.method, request.user, model_cls
        )

    def has_object_action_permission(self, action, user, obj):
        """ Check if user has permission to access action on obj for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """

        message = 'has_object_action_permission() must be implemented on {}'.format(self)
        raise NotImplementedError(message)

    def has_action_permission(self, action, user, model_cls, parent=None):
        """ Check if user has permission to access action for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """

        message = 'has_action_permission() must be implemented on {}'.format(self)
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

    def has_object_action_permission(self, action, user, obj):
        return self.has_action_permission(action, user, obj.__class__)

    def has_action_permission(self, action, user, model_cls, parent=None):
        perms = self.get_required_permissions(action, model_cls)
        return user.has_perms(perms)


class OwnerPermission(BasePermission):
    """ Allows access only to obj owner. """

    def has_object_action_permission(self, action, user, obj):
        return user == obj.owner

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True


class OwnerOrReadOnlyPermission(OwnerPermission):
    """ Allows access only to obj owner or read only. """

    def has_object_action_permission(self, action, user, obj):
        if action in permissions.SAFE_METHODS:
            return True

        return user == obj.owner

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True


class OwnerOrAdminPermission(OwnerPermission):
    """ Allows access only to obj owner and admin users. """

    def has_object_action_permission(self, action, user, obj):
        return user == obj.owner or user.is_staff


class RelatedResourceOwnerPermission(BasePermission):
    """ Allows access only to obj owner of related resource.

    This class assumes the child resource has a `parent` property which will return the parent object.
    """

    def has_permission(self, request, view):
        """ This action is called from the views which include this permission.

        The call happens during view initalisation so it will be called with views returning
        a data set as well as a single object.

        Return `True` if permission is granted, `False` otherwise.
        """

        parent = self.get_parent_from_request(request)

        return self.has_action_permission(
            request.method, request.user, view.model, parent
        )

    def get_parent_from_request(self, request):
        """ For requests to list endpoints, eg when creating an object then
        get_parent needs to be defined to use this permission class.
        """

        raise NotImplementedError('get_parent_from_request() must be implemented')

    def has_object_action_permission(self, action, user, obj):
        return user == obj.parent.owner

    def has_action_permission(self, action, user, model_cls, parent=None):
        """ Read permissions are allowed to any request, so we'll< always allow
        GET, HEAD or OPTIONS requests.
        """

        assert parent is not None, (
            'You must pass a parent when calling `has_action_permission` on RelatedResourceOwnerPermission'
        )

        if action != 'POST':
            return True

        return user == parent.owner


class OwnerOrParentOwnerOrAdminPermission(RelatedResourceOwnerPermission):
    """ Allows access only to obj owner, parent owner and admin users. """

    def has_object_action_permission(self, action, user, obj):
        result = (
            user == obj.owner or
            user.is_staff
        )

        if hasattr(obj, 'parent'):
            result = (obj == obj.parent or result)

        return result


class TenantConditionalOpenClose(BasePermission):
    """ Allows access only to authenticated users. """

    def has_object_action_permission(self, action, user, obj):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True

    def has_action_permission(self, action, user, model_cls, parent=None):
        try:
            if get_tenant_properties('CLOSED_SITE'):
                return user and user.is_authenticated()
        except AttributeError:
            pass
        return True


class IsAuthenticated(BasePermission):
    """ Allow access if the user is authenticated. """

    def has_object_action_permission(self, action, user, obj):
        return self.has_action_permission(action, user, obj)

    def has_action_permission(self, action, user, model_cls, parent=None):
        return user.is_authenticated and user.groups.filter(name='Authenticated').exists()


class AuthenticatedOrReadOnlyPermission(IsAuthenticated):
    """ Allow access if the user is authenticated or the request uses a safe action. """

    def has_action_permission(self, action, user, model_cls, parent=None):
        if action in permissions.SAFE_METHODS:
            return True

        return user.is_authenticated and user.groups.filter(name='Authenticated').exists()
