# coding=utf-8
import json

from django.core.exceptions import ImproperlyConfigured

from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.payments.exception import PaymentException

from lipisha import Lipisha, lipisha

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.models import OrderPayment
from bluebottle.payments_lipisha.models import LipishaProject
from bluebottle.utils.utils import StatusDefinition

from .models import LipishaPayment


class LipishaPaymentAdapter(BasePaymentAdapter):
    card_data = {}

    STATUS_MAPPING = {
        'Requested': StatusDefinition.CREATED,
        'Completed': StatusDefinition.SETTLED,
        'Cancelled': StatusDefinition.CANCELLED,
        'Voided': StatusDefinition.FAILED,
        'Acknowledged': StatusDefinition.AUTHORIZED,
        'Authorized': StatusDefinition.AUTHORIZED,
        'Settled': StatusDefinition.SETTLED,
        'Reversed': StatusDefinition.REFUNDED
    }

    def __init__(self, order_payment):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        if self.live_mode:
            env = lipisha.PRODUCTION_ENV
        else:
            env = lipisha.SANDBOX_ENV
        super(LipishaPaymentAdapter, self).__init__(order_payment)
        self.client = Lipisha(
            self.credentials['api_key'],
            self.credentials['api_signature'],
            api_environment=env
        )

    def _get_mapped_status(self, status):
        return self.STATUS_MAPPING[status]

    def _get_payment_reference(self):
        return "{}#{}".format(
            self.credentials['account_number'],
            self.payment.reference
        )

    def create_payment(self):
        payment = LipishaPayment(
            order_payment=self.order_payment,
        )
        payment.reference = self.order_payment.id
        payment.save()
        self.payment_logger.log(payment,
                                'info',
                                'payment_tracer: {}, '
                                'event: payment.lipisha.create_payment.success'.format(self.payment_tracer))

        self.payment = payment
        return payment

    def get_authorization_action(self):

        if self.payment.status == 'started':
            return {
                'type': 'process',
                'payload': {
                    'business_number': self.credentials['business_number'],
                    'account_number': self._get_payment_reference(),
                    'amount': int(float(self.order_payment.amount))
                }
            }
        else:
            self.check_payment_status()
            if self.payment.status in ['settled', 'authorized']:
                return {
                    'type': 'success'
                }
            else:
                return {
                    'type': 'pending'
                }

    def check_payment_status(self):

        response = self.client.get_transactions(
            transaction_type='Payment',
            transaction_reference=self.payment.reference
        )

        self.payment.response = json.dumps(response)
        data = response['content']

        if len(data) > 1:
            raise PaymentException('Payment could not be verified yet. Multiple payments found.')
        if len(data) == 0:
            raise PaymentException('Payment could not be verified yet. Payment not found.')
        else:
            payment = data[0]
            for k, v in payment.iteritems():
                setattr(self.payment, k, v)

        self.payment.status = self._get_mapped_status(self.payment.transaction_status)

        if self.payment.status in ['settled', 'authorized']:
            self.order_payment.set_authorization_action({'type': 'success'})

        self.payment.save()


class LipishaPaymentInterface(object):
    @property
    def credentials(self):
        for account in properties.MERCHANT_ACCOUNTS:
            if account['merchant'] == 'lipisha' and account['currency'] == 'KES':
                return account
        raise ImproperlyConfigured('No merchant account for Lipisha KES')

    def _get_client(self):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        if self.live_mode:
            env = lipisha.PRODUCTION_ENV
        else:
            env = lipisha.SANDBOX_ENV
        client = Lipisha(
            self.credentials['api_key'],
            self.credentials['api_signature'],
            api_environment=env
        )
        return client

    def create_account_number(self, project):
        client = self._get_client()

        response = client.create_payment_account(
            transaction_account_type=1,
            transaction_account_name=project.slug,
            transaction_account_manager=self.credentials['channel_manager']
        )

        """
        {
            u'content': {
                u'transaction_account_manager': u'test_account',
                u'transaction_account_name': u'MPESA Payments',
                u'transaction_account_number': u'09999',
                u'transaction_account_type': u'1'
            },
            u'status': {
                u'status': u'SUCCESS',
                u'status_code': 0,
                u'status_description': u'Account Created'
            }
        }
        """

        try:
            account_number = response['content']['transaction_account_number']

            LipishaProject.objects.create(
                project=project,
                account_number=account_number
            )
        except KeyError:
            raise PaymentException("Could not create an account number at Lipisha")

    def initiate_payment(self, data):
        """
        data

        api_key	Your Lipisha API key.	3aa67677e8bf1d4c8fe886a38c03a860
        api_signature	Your Lipisha API signature.	SYetmwsNnb5bwaZRyeQKhZNNkCoEx+5x=
        api_version	Version of the API	2.0.0
        api_type	Type of handshake or callback	Initiate
        transaction	Unique transaction idenitifier.	CU79AW109D
        transaction_reference	Similar to transaction	CU79AW109D
        transaction_type	Payment, Payout, Reversal, Settlement
        transaction_country	KE (Kenya), RW (Rwanda), UG (Uganda), TZ (Tanzania)
        transaction_method	Method used to carry out a transaction.
        transaction_date	Date and time of the transaction. In the format: YYYY-MM-DD HH:mm:ss 013-02-02 12:30:45
        transaction_currency	Currency of the transaction. In 3 letter international ISO format.
        transaction_amount	Value of the transaction.	100.00
        transaction_paybill	Paybill, business number, till number, merchant nickname,
            or merchant number used for the transaction	961700
        transaction_paybill_type	Type of the Paybill. Options are: Shared, Dedicated
        transaction_account	Number of the transaction account.	000075
        transaction_account_number	Similar to transaction_account	000075
        transaction_account_name	Name of the transaction account.	Test Account
        transaction_merchant_reference	Reference a person or entity used when executing a transaction.
            E.g. invoice, receipt, member number	LS0009
        transaction_name	Name of the person or entity that made a transaction.	JOHN JANE DOE
        transaction_mobile	Mobile number of the person or entity that made a transaction.	254722002222
        transaction_email	Email of the person or entity that made a transaction.	test@test.com
        transaction_code	Unique code returned by the mobile money network or financial service provider
            E.g the M-Pesa confirmation code	CU79AW109D
        transaction_status	Status of a transaction. Options are: Completed, Failed

        Response
        {
            u'transaction_reversal_status_id': u'1',
            u'transaction_amount': u'2000.0000',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction': u'04CB4F9FF',
            u'transaction_account_number': u'03858',
            u'transaction_mobile_number': u'31715283569',
            u'transaction_name': u'ROSE ONESMUS RACHEL',
            u'transaction_type': u'Payment',
            u'transaction_date': u'2017-05-19 12:43:53',
            u'transaction_reversal_status': u'None',
            u'transaction_currency': u'KES',
            u'transaction_status': u'Completed',
            u'transaction_reference': u'65689',
            u'transaction_email': u'',
            u'transaction_account_name': u'Primary'
        }
        """
        account_number = data['transaction_account']
        transaction_reference = data['transaction_reference']

        # If account number has a # then it is a donation started at our platform
        if transaction_reference:
            try:
                order_payment = OrderPayment.objects.get(pk=transaction_reference)
                return order_payment.payment
            except OrderPayment.DoesNotExist:
                # OrderPayment not found, probably not correctly filled in,
                # continue as an new anonymous donation
                pass

        try:
            lipisha_project = LipishaProject.objects.get(account_number=account_number)
        except LipishaProject.DoesNotExist:
            pass

        order = Order.objects.create()
        Donation.objects.create(order=order, project=lipisha_project.project)

        # TODO:
        # Create order payment + payment here
