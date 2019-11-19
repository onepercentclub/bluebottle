from rest_framework import permissions

from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
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
        if request.method != 'POST':
            return perm
        # If it is a POST/create request we should check Initiative related permissions
        # For PATCH/PUT this will be handled by has_object_action_permission
        try:
            initiative_id = request.data['initiative']['id']
            initiative = Initiative.objects.get(id=initiative_id)
            return perm and request.user in (
                initiative.activity_manager,
                initiative.owner)
        except KeyError, Initiative.DoesNotExist:
            return False

    def has_object_action_permission(self, action, user, obj):
        perms = self.get_required_permissions(action, obj.__class__)
        if action in permissions.SAFE_METHODS:
            return user.has_perms(perms)
        else:
            return user.has_perms(perms) and user in [
                obj.owner,
                obj.initiative.owner,
                obj.initiative.activity_manager
            ]


class ActivityTypePermission(ResourcePermission):
    def has_permission(self, request, view):
        (settings, _) = InitiativePlatformSettings.objects.get_or_create()

        if request.method == 'POST':
            return view.model.__name__.lower() in settings.activity_types
        return True


class ApplicantPermission(ResourcePermission):

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
        else:
            return user.has_perms(perms) and user in [
                obj.activity.owner,
                obj.activity.initiative.owner,
                obj.activity.initiative.activity_manager
            ]
