from celery import shared_task

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.services import PaymentService


@shared_task
def check_payment_statuses(order_payments):
    for order_payment in order_payments:
        service = PaymentService(order_payment)
        try:
            service.check_payment_status()
        except (PaymentException, TypeError):
            pass
