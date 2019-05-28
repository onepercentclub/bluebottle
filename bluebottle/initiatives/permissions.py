from rest_framework import permissions

from bluebottle.utils.permissions import ResourcePermission


class InitiativePermission(ResourcePermission):
    """
    Allows read access according to permissions
    Allows write according permissions and ownership
    """
    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_own_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_own_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_own_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_own_%(model_name)s'],
    }

    def has_object_action_permission(self, action, user, obj):
        perms = self.get_required_permissions(action, obj.__class__)
        if action in permissions.SAFE_METHODS:
            return user.has_perms(perms)
        return user.has_perms(perms) and user == obj.owner

    def has_action_permission(self, action, user, model_cls):
        perms = self.get_required_permissions(action, model_cls)
        return user.has_perms(perms)
