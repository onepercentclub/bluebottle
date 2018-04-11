from rest_framework import permissions

from bluebottle.utils.permissions import (
    BasePermission, RelatedResourceOwnerPermission, ResourceOwnerPermission
)


class RelatedProjectTaskManagerPermission(RelatedResourceOwnerPermission):
    def has_parent_permission(self, action, user, parent, model=None):
        return user == parent.task_manager


class IsEditableOrReadOnly(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if not obj:
            return True

        if action in permissions.SAFE_METHODS:
            return True
        return obj.status.editable

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_parent_permission(self, method, user, parent, model=None):
        return self.has_object_action_permission(method, user, parent)


class CanEditOwnRunningProjects(ResourceOwnerPermission):
    """ Allows access only to obj owner. """
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': [],
        'PUT': ['%(app_label)s.api_change_own_running_%(model_name)s'],
        'PATCH': [],
        'DELETE': [],
    }

    def has_object_action_permission(self, action, user, obj):
        return super(CanEditOwnRunningProjects, self).has_object_action_permission(
            action, user, obj
        ) and obj.status.slug in ('campaign', 'voting')

    def has_parent_permission(self, method, user, parent, model=None):
        return self.has_object_action_permission(method, user, parent)


class CanExportSupportersPermission(ResourceOwnerPermission):
    """ Allows access only to obj owner. """
    perms = ['projects.export_supporters']

    def has_action_permission(self, action, user, model_cls):
        return user.has_perms(self.perms)
