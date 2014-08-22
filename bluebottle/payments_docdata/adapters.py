import logging
from bluebottle.payments.adapters import AbstractPaymentAdapter
from bluebottle.payments_docdata.exceptions import MerchantTransactionIdNotUniqueException
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from interface import DocdataInterface
from django.conf import settings
from .models import DocdataPayment

logger = logging.getLogger(__name__)
payment_docdata_logger = logging.getLogger('payment.docdata')


class DocdataPaymentAdapter(AbstractPaymentAdapter):

    def __init__(self, *args, **kwargs):
        super(DocdataPaymentAdapter, self).__init__(*args, **kwargs)
        self.payment_logger = PaymentLogAdapter(payment_docdata_logger)

    @staticmethod
    def create_payment(order_payment, integration_data):
        payment = DocdataPayment(order_payment=order_payment)
        payment.total_gross_amount = order_payment.amount

        interface = DocdataInterface(debug=True)
        user = order_payment.order.user

        merchant_order_id = order_payment.id
        result = None
        t = 1

        # Docdata will need an unique id
        # Since we might send the same order-payment multiple times to Dd,
        # make sure we catch and resolve errors.
        while not result:
            merchant_order_id = "{0}-{1}".format(order_payment.id, t)
            try:
                # FIXME: Replace some hardcoded values here with actual values.
                result = interface.new_payment_cluster(
                    merchant_name=settings.DOCDATA_MERCHANT_NAME,
                    merchant_password=settings.DOCDATA_MERCHANT_PASSWORD,
                    merchant_transaction_id=merchant_order_id,
                    profile='webmenu',
                    client_id=user.id,
                    price=order_payment.amount,
                    cur_price='EUR',
                    client_email=user.email,
                    client_firstname=user.full_name,
                    client_lastname=user.full_name,
                    client_address='Unkown',
                    client_zip='Unkown',
                    client_city='Unkown',
                    client_country='NL',
                    client_language='en',
                    days_pay_period=5
                )
            except MerchantTransactionIdNotUniqueException:
                t += 1

        payment.merchant_order_id = merchant_order_id
        payment.payment_cluster_key = result['payment_cluster_key']
        payment.payment_cluster_id = result['payment_cluster_id']
        payment.save()

        return True


    @staticmethod
    def get_authorization_action(order_payment):

        payment = DocdataPayment.objects.filter(order_payment=order_payment).all()[0]

        interface = DocdataInterface(debug=True)
        url = interface.get_payment_url(payment)

        # url = interface.show_payment_cluster_url(
        #     merchant_name=settings.DOCDATA_MERCHANT_NAME,
        #     payment_cluster_key=payment.payment_cluster_key,
        #     #payment_cluster_id=payment.payment_cluster_id,
        #     #merchant_transaction_id=payment.merchant_order_id,
        # )

        return {'type': 'redirect', 'method': 'get', 'url': url}

