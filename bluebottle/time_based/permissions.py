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
            owner = obj.team.owner
        except Team.owner.RelatedObjectDoesNotExist:
            owner = None

        try:
            activity_owner = obj.team.activity.owner
        except Activity.owner.RelatedObjectDoesNotExist:
            activity_owner = None

        return (
            user
            in [
                owner,
                activity_owner,
                obj.team.activity.initiative.owner,
            ]
            or user in obj.team.activity.initiative.activity_managers.all()
        )


class SlotParticipantPermission(IsOwner):
    def has_object_action_permission(self, action, user, obj):
        return not obj.participant or user == obj.participant.user

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        return not obj.participant or request.user == obj.participant.user


class InviteCodePermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        return str(obj.invite_code) == str(obj.team.invite_code)

    def has_action_permission(self, action, user, model_cls):
        return True


class DateSlotActivityStatusPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        return (
            action not in ('POST', 'DELETE', 'PATCH', 'PUT') or
            obj.activity.owner == user or
            user in obj.activity.initiative.activity_managers.all() or
            obj.activity.initiative.owner == user or
            user.is_staff or
            user.is_superuser
        )

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            request.method not in ('POST', 'DELETE', 'PATCH', 'PUT') or
            obj.activity.owner == user or
            user in obj.activity.initiative.activity_managers.all() or
            obj.activity.initiative.owner == user or
            user.is_staff or
            user.is_superuser
        )


class ParticipantDocumentPermission(permissions.DjangoModelPermissions):

    def has_object_permission(self, request, view, obj):
        if not obj:
            return True
        if obj and (
            request.user in [
                obj.user,
                obj.activity.owner,
            ] or
            request.user in obj.activity.initiative.activity_managers.all()
        ):
            return True
        return False


class CanExportParticipantsPermission(IsOwner):
    """ Allows access only to obj owner. """

    def has_object_action_permission(self, action, user, obj):
        return (
            obj.owner == user or
            user in obj.initiative.activity_managers.all() or
            obj.initiative.owner == user or
            user.is_staff or
            user.is_superuser
        ) and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True
