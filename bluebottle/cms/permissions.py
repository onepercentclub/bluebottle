from bluebottle.members.models import MemberPlatformSettings
from bluebottle.utils.permissions import BasePermission


class PlatformPagePermission(BasePermission):

    def has_permission(self, request, view):
        page = view.get_object()
        settings = MemberPlatformSettings.load()
        if (
            settings.closed
            and (not request.user or not request.user.is_authenticated)
            and page.slug == 'start'
        ):
            return False

        return True

    def __repr__(self):
        return 'PlatformPagePermission'
