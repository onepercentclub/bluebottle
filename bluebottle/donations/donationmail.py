import logging

from django.utils.translation import ugettext as _

from bluebottle.payments.models import Payment

logger = logging.getLogger(__name__)


def get_payment_method(donation):
    order_payments = donation.order.order_payments.all()

    try:
        payment_method = order_payments[0].payment.method_name
    except Payment.DoesNotExist:
        # TODO: we need to properly handle the payment method
        #       name here. Pledges will end up here but the
        #       payment_method will be something like
        #       'pledgeStandard'...
        payment_method = order_payments[0].payment_method
        if 'pledge' in payment_method:
            payment_method = _('Invoiced')
    except IndexError:
        payment_method = ''

    return payment_method
