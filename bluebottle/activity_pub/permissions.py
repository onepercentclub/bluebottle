from rest_framework import permissions

from bluebottle.activity_pub.models import Follow, Accept
from bluebottle.members.models import MemberPlatformSettings


class ActivityPubPermission(permissions.BasePermission):
    def has_permission(self, request, view=None):
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
    def has_permission(self, request, view=None):
        if request.method == 'POST':
            if hasattr(request, 'data') and isinstance(request.data, dict) and 'type' in request.data:
                if request.data['type'] == 'Follow':
                    return True
                if request.data['type'] in ('Publish', 'Accept'):
                    # Only actors we follow can post publish activities
                    return Follow.objects.filter(object=request.auth).exists()
                if request.data['type'] in ('Announce', ):
                    # Only actors that we accepted us can announce
                    return Accept.objects.filter(object__actor=request.auth).exists()

            return False
        else:
            return True
