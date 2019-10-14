from bluebottle.utils.permissions import BasePermission


class PledgePaymentPermission(BasePermission):
    def has_permission(self, request, view):
        """ This action is called from the views which include this permission.

        The call happens during view initialisation so it will be called with views returning
        a data set as well as a single object.

        Return `True` if permission is granted, `False` otherwise.
        """
        return request.user.is_authenticated and request.user.can_pledge

    def has_object_action_permission(self, action, user, obj):
        """ Check if user has permission to access action on obj for the view.

        Used by both the DRF permission system and for returning permissions to the user.
        """
        return user.is_authenticated and user.can_pledge
