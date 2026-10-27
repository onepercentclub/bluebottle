from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.permissions import ResourcePermission, ResourceOwnerPermission, BasePermission


class InitiativeStatusPermission(ResourcePermission):
    def has_object_action_permission(self, action, user, obj):
        if (
            action in ('PATCH', 'PUT') and
            obj.status in ('rejected', 'deleted', 'cancelled', 'submitted')
        ):
            return False
        else:
            return True

    def has_action_permission(self, action, user, model_cls):
        return True


class InitiativeOwnerPermission(ResourceOwnerPermission):
    """ Allows access only to initiative owner and activity managers"""
    def has_object_action_permission(self, action, user, obj):
        return (
            user == obj.owner or
            user in obj.activity_managers.all() or
            user.is_staff or
            user.is_superuser
        )


class ContactActivityManagerPermission(BasePermission):

    def has_permission(self, request, view):
        settings = InitiativePlatformSettings.load()
        return settings.contact_activity_manager

    def __repr__(self):
        return 'ContactActivityManagerPermission'

    def has_object_action_permission(self, action, user, obj):
        return True
