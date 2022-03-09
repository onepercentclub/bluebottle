from bluebottle.utils.permissions import BasePermission


class OpenSegmentOrMember(BasePermission):

    def has_action_permission(self, action, user, model_cls):
        return True

    def has_object_action_permission(self, method, user, obj):

        return (
            not obj.closed or
            user.is_staff or
            (user.is_authenticated and obj in user.segments.all())
        )
