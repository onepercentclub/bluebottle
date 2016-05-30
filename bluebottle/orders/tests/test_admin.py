import mock

from django.db.models.query import QuerySet

from bluebottle.orders.models import Order
from bluebottle.test.utils import BluebottleTestCase

from ..admin import OrderStatusFilter, BaseOrderAdmin


def generate_order_test(id):
    """ Generate a test for a specific order state id and return it """

    def generated_test(self):
        """ if a valid state is passed, it must become part of the query """
        filter = OrderStatusFilter(None, {'status__exact': id},
                                   Order, BaseOrderAdmin)
        queryset = mock.Mock(spec=QuerySet)

        filter.queryset({}, queryset)

        self.failUnless(queryset.filter.call_args)  # has it been called?
        self.failUnless(queryset.filter.call_args[1] == {'status': id})

    return generated_test


class OrderTestMeta(type):
    """ Test the filter on all Order states by iterating over STATUS_CHOICES
        and create an individual test case for each state """

    def __init__(cls, what, bases=None, dict=None):
        super(OrderTestMeta, cls).__init__(what, bases, dict)

        for (id, label) in Order.STATUS_CHOICES:
            setattr(cls, 'test_query_state_' + id, generate_order_test(id))


class OrderTestAdmin(BluebottleTestCase):
    """ Test all states in Order. The actual test methods are created in the
        meta class """
    __metaclass__ = OrderTestMeta
