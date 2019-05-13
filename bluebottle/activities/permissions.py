from bluebottle.utils.permissions import ResourceOwnerPermission


class ActivityPermission(ResourceOwnerPermission):
    """
    Allows access only to obj owner of related initiative.
    """
    view = None
    request = None

    def has_parent_permission(self, action, user, initiative, model=None):
        return user == initiative.owner

    def has_object_action_permission(self, action, user, obj):
        return self.has_parent_permission(action, user, obj.initiative)

    def has_action_permission(self, action, user, model_cls):
        perms = self.get_required_permissions(action, model_cls)
        return user.has_perms(perms)

    def has_permission(self, request, view):
        return True
        self.view = view
        self.request = request
        return super(ActivityPermission, self).has_permission(request, view)
