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
