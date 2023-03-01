from bluebottle.initiatives.models import InitiativePlatformSettings
from rest_framework import permissions
from bluebottle.utils.permissions import IsOwner, BasePermission


class SlotParticipantPermission(IsOwner):
    def has_object_action_permission(self, action, user, obj):
        return user == obj.participant.user

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.participant.user


class DateSlotActivityStatusPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        return (
            action not in ('POST', 'DELETE') or
            obj.activity.status in ['draft', 'needs_work', 'submitted', 'open']
        )

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_permission(self, request, view, obj):
        return (
            request.method not in ('POST', 'DELETE') or
            obj.activity.status in ['draft', 'needs_work', 'submitted']
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
        return (obj.owner == user or user in obj.initiative.activity_managers.all()) \
            and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True
