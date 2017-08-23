from rest_framework import permissions
from bluebottle.utils.permissions import BasePermission


class NoDonationsOrReadOnly(BasePermission):
    """
    If a reward has no donations it should be editable/deletable
    """
    def has_object_action_permission(self, method, view, obj=None, parent=None):
        if method in permissions.SAFE_METHODS:
            return True

        if obj:
            return not obj.count

        return True

    def has_action_permission(self, action, user, model):
        return True
