from rest_framework import permissions

from bluebottle.utils.utils import get_class
from bluebottle.utils.permissions import BasePermission, RelatedResourceOwnerPermission


class RelatedProjectOwnerPermission(RelatedResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return user == parent.owner

    def has_action_permissions(self, *args, **kwargs):
        return True



class RelatedProjectTaskManagerPermission(RelatedResourceOwnerPermission):

    def has_object_action_permission(self, action, user, obj=None, parent=None):
        if obj:
            parent = obj.parent

        return user == parent.task_manager


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


class IsProjectWallOwner(permissions.BasePermission):
    """
    Allows access only to project owner.
    """

    def has_object_permission(self, request, view, obj):
        return obj.mediawallpost.content_object.owner == request.user
