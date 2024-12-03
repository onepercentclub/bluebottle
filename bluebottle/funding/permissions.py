from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.utils.permissions import IsOwner


class DonorOwnerOrSucceededPermission(IsOwner):
    def has_object_permission(self, request, view, obj):
        settings = MemberPlatformSettings.objects.get()
        if (not settings.closed or request.user.is_authenticated) \
                and obj.status == 'succeeded' and request.method == 'GET':
            return True

        if not request.user.is_authenticated and request.auth and obj.client_secret:
            return obj.client_secret == request.auth

        return super(DonorOwnerOrSucceededPermission, self).has_object_permission(request, view, obj)


class PaymentPermission(IsOwner):
    def has_object_permission(self, request, view, obj):
        if (
            not request.user.is_authenticated and
            request.auth and
            obj.donation.client_secret
        ):
            return obj.donation.client_secret == request.auth

        return super().has_object_permission(request, view, obj.donation)


class IntentPermission(IsOwner):
    def has_object_permission(self, request, view, obj):
        if (
            not request.user.is_authenticated and
            request.auth and
            obj.donation.client_secret
        ):
            return obj.client_secret == request.auth

        return super().has_object_permission(request, view, obj.donation)


class CanExportSupportersPermission(IsOwner):
    """ Allows access only to obj owner. """
    def has_object_action_permission(self, action, user, obj):
        return (obj.owner == user or user in obj.initiative.activity_managers.all()) \
            and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True
