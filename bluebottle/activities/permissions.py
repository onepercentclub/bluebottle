from rest_framework import permissions

from bluebottle.activities.models import Activity
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.permissions import ResourcePermission, ResourceOwnerPermission, BasePermission


class ActivityOwnerPermission(ResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj):
        try:
            owner = obj.owner
        except Activity.owner.RelatedObjectDoesNotExist:
            owner = None

        is_owner = user in [
            owner,
            obj.initiative.owner,
        ] or user in obj.initiative.activity_managers.all()

        if action == 'POST':
            return is_owner or (obj.initiative.status == 'approved' and obj.initiative.is_open)
        else:
            return is_owner


class RelatedActivityOwnerPermission(ResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj):
        activity = obj.activity
        try:
            owner = activity.owner
        except Activity.owner.RelatedObjectDoesNotExist:
            owner = None

        is_owner = user in [
            owner,
            activity.initiative.owner,
        ] or user in activity.initiative.activity_managers.all()

        return is_owner


class ActivityTypePermission(ResourcePermission):
    def has_permission(self, request, view):
        (settings, _) = InitiativePlatformSettings.objects.get_or_create()

        if request.method == 'POST':
            activity_type = view.model.__name__.lower()
            if activity_type == 'collectactivity':
                activity_type = 'collect'
            return activity_type in settings.activity_types

        return True


class ActivityStatusPermission(ResourcePermission):
    def has_object_action_permission(self, action, user, obj):
        if (
            action in ('PATCH', 'PUT') and
            obj.status in ('rejected', 'deleted')
        ):
            return False
        else:
            return True

    def has_action_permission(self, action, user, model_cls):
        return True


class ActivitySegmentPermission(BasePermission):

    def has_object_action_permission(self, action, user, obj):
        activity_segments = obj.segments.filter(closed=True)
        if activity_segments:
            if not user.is_authenticated:
                return False
            elif user.is_staff:
                return True
            elif any(
                    segment in activity_segments for segment in user.segments.filter(closed=True)
            ):
                return True
            else:
                return False
        else:
            return True

    def has_action_permission(self, action, user, model_cls):
        return True


class ContributorPermission(ResourcePermission):

    perms_map = {
        'GET': ['%(app_label)s.api_read_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': ['%(app_label)s.api_read_%(model_name)s'],
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
            ] or user in obj.activity.initiative.activity_managers.all()


class ContributionPermission(ResourcePermission):

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_action_permission(self, action, user, obj):
        return user in [
            obj.contributor.activity.owner,
            obj.contributor.activity.initiative.owner,
        ] or user in obj.contributor.activity.initiative.activity_managers.all()


class IsAdminPermission(ResourcePermission):

    def has_action_permission(self, action, user, model_cls):
        return user.is_staff or user.is_superuser

    def has_object_action_permission(self, action, user, obj):
        return user.is_staff or user.is_superuser


class DeleteActivityPermission(ResourcePermission):
    def has_object_action_permission(self, action, user, obj):
        if (
            action == 'DELETE' and
            obj.status not in ('draft', 'needs_work', )
        ):
            return False
        else:
            return True

    def has_action_permission(self, action, user, model_cls):
        return True


class CanExportTeamParticipantsPermission(IsOwner):
    """ Allows access only to team owner or activity manager. """
    def has_object_action_permission(self, action, user, obj):
        return (
            obj.owner == user or
            obj.activity.owner == user or
            user in obj.activity.initiative.activity_managers.all()
        ) and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True
