from rest_framework import permissions

from bluebottle.activity_pub.models import ActivityPubModel, Follow, Accept
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
                if request.data['type'] in (
                    'Create', 'Update', 'Cancel', 'Finish', 'Delete'
                ):
                    # Only actors we follow can post publish activities
                    return Follow.objects.filter(object=request.auth).exists()
                if request.data['type'] in ('Accept', ):
                    # Only actors that we accepted us can announce
                    try:
                        object = ActivityPubModel.objects.from_iri(request.data['object'])

                        if isinstance(object, Follow):
                            return Follow.objects.filter(object=request.auth).exists()
                        else:
                            # If it's an Accept on an Event, make sure we accepted the related follow
                            return Accept.objects.filter(
                                object__in=Follow.objects.filter(actor=request.auth)
                            ).exists()
                    except ActivityPubModel.DoesNotExist:
                        return False

                    return

            return False
        else:
            return True
