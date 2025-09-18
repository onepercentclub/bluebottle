from rest_framework import permissions

from bluebottle.activity_pub.models import Follow
from bluebottle.members.models import MemberPlatformSettings


class ActivityPubPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True
        if request.method == 'GET':
            settings = MemberPlatformSettings.load()
            if settings.closed:
                if request.auth:
                    return Follow.objects.filter(object=request.auth).exists()
                else:
                    return False

            else:
                return True
        else:
            return False


class InboxPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            if request.data['type'] == 'Follow':
                return True
            if request.data['type'] in ('Publish', 'Accept'):
                # Only actors we follow can post publish activities
                return Follow.objects.filter(object=request.auth).exists()

            return False
        else:
            return True
