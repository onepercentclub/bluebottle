from rest_framework import permissions

from .models import BaseOrganization


class IsOrganizationMember(permissions.BasePermission):
    """
    Allows access only to organization members
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, BaseOrganization):
            return request.user.id in obj.members.values_list('user_id', flat=True)
        return request.user.id in obj.organization.members.values_list('user_id', flat=True)
