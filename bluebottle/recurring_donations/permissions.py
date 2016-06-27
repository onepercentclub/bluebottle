from bluebottle.recurring_donations.models import MonthlyDonor
from rest_framework import permissions
from bluebottle.clients import properties


class RecurringDonationsEnabled(permissions.BasePermission):
    """
    Check if Recurring Donations are enabled for the current Client
    """

    def has_permission(self, request, view):
        return getattr(properties, 'RECURRING_DONATIONS_ENABLED', False)

    def has_object_permission(self, request, view, obj):
        return getattr(properties, 'RECURRING_DONATIONS_ENABLED', False)


class IsOwner(permissions.BasePermission):
    """ Read / write permissions are only allowed if the obj.user is the logged in user. """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsDonor(permissions.BasePermission):
    def _get_donor_from_request(self, request):
        if request.data:
            order_id = request.data.get('donation', None)
        else:
            order_id = request.query_params.get('donation', None)
        if order_id:
            try:
                project = MonthlyDonor.objects.get(id=order_id)
                return project
            except MonthlyDonor.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        donor = self._get_donor_from_request(request)
        if donor:
            return donor.user == request.user
        return True

    def has_object_permission(self, request, view, obj):
        return obj.donor.user == request.user
