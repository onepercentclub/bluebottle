from celery import shared_task
from django.db import connection

from bluebottle.clients.utils import LocalTenant
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.services import PaymentService


@shared_task
def check_payment_statuses(order_payments, tenant):
    connection.set_tenant(tenant)

    with LocalTenant(tenant, clear_tenant=True):

        for order_payment in order_payments:
            service = PaymentService(order_payment)
            try:
                service.check_payment_status()
            except (PaymentException, TypeError):
                pass
