from bluebottle.organizations.models import Organization
from rest_framework import permissions


class IsOrganizationMember(permissions.BasePermission):
    """
    Allows access only to organization members
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Organization):
            return request.user.id in obj.members.values_list(
                'user_id', flat=True)
        return request.user.id in obj.organization.members.values_list(
            'user_id', flat=True)


class IsContactOwner(permissions.BasePermission):
    """
    allows access only to contact owner.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
