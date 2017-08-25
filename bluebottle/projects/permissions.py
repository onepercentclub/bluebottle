from rest_framework import permissions

from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedProjectTaskManagerPermission(RelatedResourceOwnerPermission):

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return user == parent.task_manager


class RelatedProjectTaskManagerOrOwnerPermission(RelatedResourceOwnerPermission):

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return user == parent.task_manager or user == parent.owner


class IsEditableOrReadOnly(BasePermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if not obj:
            return True

        if action in permissions.SAFE_METHODS:
            return True

        return obj.status.editable

    def has_action_permission(self, action, user, model_cls, parent=None):
        return True
