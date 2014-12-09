from bluebottle.utils.model_dispatcher import get_order_model
from rest_framework import permissions

from bluebottle.utils.utils import StatusDefinition

ORDER_MODEL = get_order_model()


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
    Allows the access to a payment or order only if the user created the Order that the payment belongs to.
    """
    def has_object_permission(self, request, view, obj):
        # Use duck typing to check if we have an order or a payment.
        if hasattr(obj, 'user'):
            order = obj
        else:
            order = obj.order

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
            return (order.user == request.user or order.pk == request.session.get('new_order_id'))

        # Case 2: Anonymous user.
        else:
            order_id = request.session.get('new_order_id')
            if order_id:
                return order_id == order.id
            return False

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
        if request.method in permissions.SAFE_METHODS or request.method == 'DELETE':
            return True

        if view.model == ORDER_MODEL:
            # Order must belong to the current user or have no user assigned (anonymous)
            order_user = request.DATA.get('user', None)
            if order_user and order_user != request.user.pk:
                return False
            return True
        else: # This is for creating new objects that have a relation (fk) to Order.
            order = self._get_order_from_request(request)
            if order:
                # Allow action if order belongs to user or if the user is anonymous
                # and the current order in the session is the same as this order
                if request.user.is_authenticated():
                    return (order.user == request.user or order.pk == request.session.get('new_order_id'))
                elif order.pk == request.session.get('new_order_id'):
                    return True
            else: # deny if no order present
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
        if request.method in permissions.SAFE_METHODS or request.method == 'DELETE':
            return True

        # This is for creating new objects that have a relation (fk) to Order.
        if not view.model == ORDER_MODEL:
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
        if isinstance(obj, ORDER_MODEL):
            return obj.status == StatusDefinition.CREATED
        return obj.order.status == StatusDefinition.CREATED

