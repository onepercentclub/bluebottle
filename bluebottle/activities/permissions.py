from rest_framework import permissions

from bluebottle.initiatives.models import Initiative
from bluebottle.utils.permissions import ResourceOwnerPermission


class ActivityPermission(ResourceOwnerPermission):

    def has_permission(self, request, view):
        perm = super(ActivityPermission, self).has_permission(request, view)
        if request.method in permissions.SAFE_METHODS:
            return perm
        try:
            initiative_id = request.data['initiative']['id']
            initiative = Initiative.objects.get(id=initiative_id)
            return perm and initiative.owner == request.user
        except KeyError, Initiative.DoesNotExist:
            return False
