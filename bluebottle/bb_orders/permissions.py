from bluebottle.bb_orders.models import OrderStatuses
from bluebottle.utils.model_dispatcher import get_order_model
from rest_framework import permissions

ORDER_MODEL = get_order_model()

class IsUser(permissions.BasePermission):
    """ Read / write permissions are only allowed if the obj.user is the logged in user. """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOrderCreator(permissions.BasePermission):
    """
    Allows the access to a payment or order only if the user created the Order that the payment belongs to.
    """
    def has_object_permission(self, request, view, obj):
        # Use duck typing to check if we have an order or a payment.
        if hasattr(obj, 'user'):
            order = obj
        else:
            order = obj.order

        # Case 1: Authenticated user.
        if request.user.is_authenticated():
            # Permission is only granted if the order user is the logged in user.
            return order.user == request.user

        # Case 2: Anonymous user.
        else:
            # For an anonymous user we grant access if the new order id is the same as the payment order id.
            order_id = request.session.get('new_order_id')
            if order_id:
                return order_id == order.id
            return False


class OrderIsNew(permissions.BasePermission):
    """
    Check if the Order has status new. This also works for objects that have a foreign key to order.

    """

    def _get_order_from_request(self, request):
        if request.DATA:
            order_id = request.DATA.get('order', None)
        else:
            order_id = request.QUERY_PARAMS.get('order', None)
        if order_id:
            try:
                project = ORDER_MODEL.objects.get(id=order_id)
                return project
            except ORDER_MODEL.DoesNotExist:
                return None
        else:
            return None

    def has_permission(self, request, view):
        # Allow non modifying actions
        if request.method in permissions.SAFE_METHODS:
            return True

        # This is for creating new objects that have a relation (fk) to Order.
        order = self._get_order_from_request(request)
        if order:
            return order.status == OrderStatuses.new
        return True


    def has_object_permission(self, request, view, obj):

        # Allow non modifying actions
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the object is an Order or if it some object that has a foreign key to Order.
        if isinstance(obj, ORDER_MODEL):
            return obj.status == OrderStatuses.new
        return obj.order.status == OrderStatuses.new

