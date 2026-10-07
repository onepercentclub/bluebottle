from bluebottle.utils.permissions import BasePermission


class CanExportVotesPermission(BasePermission):
    """Allows staff to export poll voting results when participant exports are enabled."""

    def has_object_action_permission(self, action, user, obj):
        return (
            user.is_authenticated
            and (user.is_staff or user.is_superuser)
        )

    def has_action_permission(self, action, user, model_cls):
        return True
