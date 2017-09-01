from rest_framework import permissions

from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


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
