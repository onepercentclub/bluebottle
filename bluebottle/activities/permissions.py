from rest_framework import permissions

from bluebottle.initiatives.models import Initiative
from bluebottle.utils.permissions import ResourcePermission


class ActivityPermission(ResourcePermission):

    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.api_add_own_%(model_name)s'],
        'PUT': ['%(app_label)s.api_change_own_%(model_name)s'],
        'PATCH': ['%(app_label)s.api_change_own_%(model_name)s'],
        'DELETE': ['%(app_label)s.api_delete_own_%(model_name)s'],
    }

    def has_permission(self, request, view):
        perm = super(ActivityPermission, self).has_permission(request, view)
        if request.method in permissions.SAFE_METHODS:
            return perm
        try:
            initiative_id = request.data['initiative']['id']
            initiative = Initiative.objects.get(id=initiative_id)
            return perm and initiative.owner == request.user
        except KeyError, Initiative.DoesNotExist:
            return False

    def has_object_action_permission(self, action, user, obj):
        perms = self.get_required_permissions(action, obj.__class__)
        if action in permissions.SAFE_METHODS:
            return perms
        else:
            return perms and user == obj.owner
