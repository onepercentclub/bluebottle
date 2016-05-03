import re

from rest_framework import permissions

from bluebottle.clients import properties
from .services import check_access_handler


class CanAccessPaymentMethod(permissions.BasePermission):
    """
    Allows access to a restricted payment method only if the user has permission.
    """

    def has_permission(self, request, view):
        # Convert camelcase to dashed
        def convert(method):
            return re.sub('([a-z0-9])([A-Z])', r'\1-\2', method).lower()

        # Find the matching payment method
        all_methods = getattr(properties, 'PAYMENT_METHODS', ())
        request_method = convert(request.DATA.get('payment_method', ''))
        methods = [method for method in all_methods if method['id'] == request_method]
        allowed = True

        if len(methods) == 1:
            try:
                handler = methods[0]['method_access_handler']
                allowed = check_access_handler(handler, request.user)

            except KeyError as e:
                # No access handler for payment method
                pass

        return allowed
