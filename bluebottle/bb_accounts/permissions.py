from bluebottle.members.models import MemberPlatformSettings
from bluebottle.utils.permissions import BasePermission


class CurrentUserPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        return user == obj

    def has_permission(self, request, view):
        return True


class IsAuthenticatedOrOpenPermission(BasePermission):
    def has_object_action_permission(self, action, user, obj):
        settings = MemberPlatformSettings.objects.get()
        return (user and user.is_authenticated) or not settings.closed

    def has_permission(self, request, view):
        settings = MemberPlatformSettings.objects.get()
        return request.user.is_authenticated or not settings.closed
