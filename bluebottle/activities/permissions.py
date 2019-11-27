from rest_framework import permissions

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.activities.models import Activity
from bluebottle.utils.permissions import ResourcePermission, ResourceOwnerPermission


class ActivityOwnerPermission(ResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj):
        try:
            owner = obj.owner
        except Activity.owner.RelatedObjectDoesNotExist:
            owner = None

        return user in [
            owner,
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
