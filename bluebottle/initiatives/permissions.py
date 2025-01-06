from bluebottle.utils.permissions import ResourcePermission, ResourceOwnerPermission


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
            super().has_object_action_permission(action, user, obj) or
            user in obj.activity_managers.all()
        )
