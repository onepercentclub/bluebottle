from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.updates.models import AudienceChoices
from bluebottle.updates.utils import get_effective_audience, user_can_view_contributor_updates


class IsAuthorPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is author of the update, `False` otherwise.
        """
        return obj.author == request.user

    def has_object_action_permission(self, method, user, obj):
        if method in SAFE_METHODS:
            return True
        return obj.author == user

    def has_action_permission(self, method, user, obj):
        return True


class IsStaffMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser

    def has_object_action_permission(self, method, user, obj):
        if method in SAFE_METHODS:
            return True
        return user.is_staff or user.is_superuser

    def has_action_permission(self, method, user, obj):
        return True


class ActivityOwnerUpdatePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is author of the update, `False` otherwise.
        """
        owners = obj.activity.owners
        audience = getattr(obj, 'audience', AudienceChoices.everyone)

        return (
            obj.author in owners or
            (not obj.notify and not obj.pinned and audience != AudienceChoices.contributors) or
            request.user.is_staff or
            request.user.is_superuser
        )


class UpdateRelatedActivityPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        activity = obj.activity
        return user in list(activity.owners)

    def has_object_action_permission(self, method, user, obj):
        if method in SAFE_METHODS:
            return True
        activity = obj.activity
        return user in list(activity.owners)

    def has_action_permission(self, method, user, obj):
        return True


class CanPostUpdatePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        settings = InitiativePlatformSettings.load()

        return (
            not settings.restrict_updates or
            request.user in list(obj.owners)
            or request.user.is_staff
        )

    def has_object_action_permission(self, method, user, obj):
        if method in SAFE_METHODS:
            return True

        settings = InitiativePlatformSettings.load()

        return (
            not settings.restrict_updates or
            user in list(obj.owners)
            or user.is_staff
        )


class ContributorAudiencePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return True

        if get_effective_audience(obj) == AudienceChoices.contributors:
            return user_can_view_contributor_updates(request.user, obj.activity)
        return True

    def has_object_action_permission(self, method, user, obj):
        if method not in SAFE_METHODS:
            return True

        if get_effective_audience(obj) == AudienceChoices.contributors:
            return user_can_view_contributor_updates(user, obj.activity)
        return True

    def has_action_permission(self, method, user, obj):
        return True
