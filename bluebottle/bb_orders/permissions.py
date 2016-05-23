from rest_framework import permissions

from bluebottle.orders.models import Order
from bluebottle.utils.utils import StatusDefinition


class LoggedInUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated():
            return True
        return False


class IsUser(permissions.BasePermission):
    """ Read / write permissions are only allowed if the obj.user is the logged in user. """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOrderCreator(permissions.BasePermission):
    """
    Allows the access to a payment or order only if the user created the Order
    that the payment belongs to.
    """

    def has_object_permission(self, request, view, obj):
        # Use duck typing to check if we have an order or a payment/donation.
        if hasattr(obj, 'order'):
            order = obj.order
        else:
            order = obj

        # Permission is granted if:
        #   * the order user is the logged in user
        #   * the order has no user but the current
        #     order in the session has the same order_id as the order being
        #     accessed. This will happen if the order was created anonymously
        #     and then the user logged in / signed up.

        # Case 1: Authenticated user.
        if request.user.is_authenticated():
            # Does the order match the current user, or do they have an order
            # in the session which matches this order?
            return (order.user == request.user or
                    order.pk == request.session.get('new_order_id'))

        # Case 2: Anonymous user.
        else:
            order_id = request.session.get('new_order_id')
            if order_id:
                return order_id == order.id
            return False

    def _get_order_from_request(self, request):
        if request.data:
            order_id = request.data.get('order', None)
        else:
            order_id = request.query_params.get('order', None)
        if order_id:
            try:
                project = Order.objects.get(id=order_id)
                return project
            except Order.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        # Allow non modifying actions
        if request.method in permissions.SAFE_METHODS or request.method == 'DELETE':
            return True

        if view.queryset.model == Order:
            # Order must belong to the current user or have no user assigned (anonymous)
            order_user_id = int(request.data.get('user', 0))
            if order_user_id and order_user_id != request.user.pk:
                return False
            return True
        else:  # This is for creating new objects that have a relation (fk) to Order.
            order = self._get_order_from_request(request)
            if order:
                # Allow action if order belongs to user or if the user is anonymous
                # and the current order in the session is the same as this order
                if request.user.is_authenticated():
                    return (order.user == request.user or order.pk ==
                            request.session.get('new_order_id'))
                elif order.pk == request.session.get('new_order_id'):
                    return True
            else:  # deny if no order present
                return False


class OrderIsNew(permissions.BasePermission):
    """
    Check if the Order has status new. This also works for objects that have a foreign key to order.

    """

    def _get_order_from_request(self, request):
        if request.data:
            order_id = request.data.get('order', None)
        else:
            order_id = request.query_params.get('order', None)
        if order_id:
            try:
                project = Order.objects.get(id=order_id)
                return project
            except Order.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        # Allow non modifying actions
        if request.method in permissions.SAFE_METHODS or request.method == 'DELETE':
            return True

        # This is for creating new objects that have a relation (fk) to Order.
        if not view.queryset.model == Order:
            order = self._get_order_from_request(request)
            if order:
                return order.status == StatusDefinition.CREATED
            else:
                return False
        return True

    def has_object_permission(self, request, view, obj):

        # Allow non modifying actions
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the object is an Order or if it some object that has a foreign key to Order.
        if isinstance(obj, Order):
            return obj.status == StatusDefinition.CREATED
        return obj.order.status == StatusDefinition.CREATED
