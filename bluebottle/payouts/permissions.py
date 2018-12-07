from bluebottle.organizations.models import Organization
from rest_framework import permissions

from bluebottle.payouts.models.plain import PayoutDocument


class IsOrganizationMember(permissions.BasePermission):
    """
    Allows access only to organization members
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Organization):
            return request.user.id in obj.organizationmember_set.values_list(
                'user_id', flat=True)
        return request.user.id in obj.organization.organizationmember_set.values_list(
            'user_id', flat=True)


class IsPayoutDocumentOwner(permissions.BasePermission):
    """
    Allows access only to document owner
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, PayoutDocument):
            return request.user == obj.author
        return True
