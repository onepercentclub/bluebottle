from bluebottle.utils.permissions import BasePermission


class CurrentUserPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        return user == obj

    def has_permission(self, request, view):
        return True
