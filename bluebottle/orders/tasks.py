import logging

from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.orders.models import Order
from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)


@shared_task
def timeout_new_order(order, tenant):
    """ Timeout new orders.

    If the order's status is still CREATED, assume that the order will
    never be finished.
    """
    logger.info("Timeing out order {}".format(order))

    with LocalTenant(tenant, clear_tenant=True):
        order = Order.objects.get(pk=order.pk)
        if order.status == StatusDefinition.CREATED:
            order.transition_to(StatusDefinition.FAILED)


@shared_task
def timeout_locked_order(order, tenant):
    """ Timeout locked orders.

    If the order's status is still LOCKED, assume the the order
    will never be  payed.
    """
    logger.info("Timeing out order {}".format(order))

    with LocalTenant(tenant, clear_tenant=True):
        order = Order.objects.get(pk=order.pk)
        if order.status == StatusDefinition.LOCKED:
            order.transition_to(StatusDefinition.FAILED)
