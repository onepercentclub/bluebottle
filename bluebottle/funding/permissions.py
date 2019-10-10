from bluebottle.utils.permissions import IsOwner


class DonationOwnerPermission(IsOwner):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated and request.auth and obj.client_secret:
            return obj.client_secret == request.auth

        return super(DonationOwnerPermission, self).has_object_permission(request, view, obj)


class PaymentPermission(IsOwner):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated and request.auth and obj.donation.client_secret:
            return obj.donation.client_secret == request.auth

        return super(PaymentPermission, self).has_object_permission(request, view, obj.donation)


class CanExportSupportersPermission(IsOwner):
    """ Allows access only to obj owner. """
    def has_object_action_permission(self, action, user, obj):
        return obj.owner == user or obj.initiative.activity_manager == user
