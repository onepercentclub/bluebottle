from rest_framework import permissions

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.time_based.models import Team
from bluebottle.activities.models import Activity
from bluebottle.utils.permissions import (
    IsOwner,
    BasePermission,
    ResourceOwnerPermission,
)


class TeamMemberPermission(ResourceOwnerPermission):
    def has_object_action_permission(self, action, user, obj):
        try:
            captain = obj.team.owner
        except Team.owner.RelatedObjectDoesNotExist:
            captain = None

        try:
            activity_owners = obj.team.activity.owners
        except Activity.owner.RelatedObjectDoesNotExist:
            activity_owners = []

        return (
            user == captain or
            user in activity_owners or
            user.is_staff or
            user.is_superuser
        )


class DateParticipantPermission(IsOwner):
    def has_object_action_permission(self, action, user, obj):
        return user == obj.user

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user


class CreateByEmailPermission(IsOwner):
    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        if request.data.get('email', None):
            return request.user.is_staff or request.user.is_superuser
        return True


class InviteCodePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            str(obj.invite_code) == str(obj.team.invite_code) or
            request.user.is_staff or
            request.user.is_superuser or
            request.user == obj.team.owner
        )

    def has_action_permission(self, action, user, model_cls):
        return True


class DateSlotActivityStatusPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        return (
            action not in ('POST', 'DELETE', 'PATCH', 'PUT') or
            user in obj.activity.owners or
            user.is_staff or
            user.is_superuser
        )

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            request.method not in ('POST', 'DELETE', 'PATCH', 'PUT') or
            user in obj.activity.owners or
            user.is_staff or
            user.is_superuser
        )


class ParticipantDocumentPermission(permissions.DjangoModelPermissions):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not obj:
            return True
        if obj and (
            user == obj.user or
            user in obj.activity.owners or
            user.is_staff or
            user.is_superuser

        ):
            return True
        return False


class CanExportParticipantsPermission(IsOwner):
    """ Allows access only to obj owner. """

    def has_object_action_permission(self, action, user, obj):
        return (
            user in obj.owners or
            user.is_staff or
            user.is_superuser
        ) and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True
