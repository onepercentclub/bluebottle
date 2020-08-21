from bluebottle.utils.permissions import ResourcePermission


class InitiativeStatusPermission(ResourcePermission):
    def has_object_action_permission(self, action, user, obj):
        if (
            action in ('PATCH', 'PUT') and
            obj.status in ('rejected', 'deleted', 'cancelled')
        ):
            return False
        else:
            return True

    def has_action_permission(self, action, user, model_cls):
        return True
