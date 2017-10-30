# coding=utf-8
import json
from lipisha import Lipisha, lipisha
from moneyed.classes import Money

from django.core.exceptions import ImproperlyConfigured

from bluebottle.clients import properties
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
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
            merchant_transaction_reference=self.payment.reference
        )
        self.payment.response = json.dumps(response)
        data = response['content']

        if len(data) > 1:
            pass
            # raise PaymentException('Payment could not be verified yet. Multiple payments found.')
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

    def generate_response(self, payment):
        donation = payment.order_payment.order.donations.first()
        message = "Dear {}, thanks for your donation {} of {} {} to {}!".format(
            donation.name,
            payment.transaction_reference,
            payment.transaction_currency,
            payment.transaction_amount,
            donation.project.title
        )

        return {
            "api_key": self.credentials['api_key'],
            "api_signature": self.credentials['api_signature'],
            "api_version": "1.0.4",
            "api_type": "Payment",
            "transaction_reference": payment.reference,
            "transaction_status_code": "001",
            "transaction_status": "SUCCESS",
            "transaction_status_description": "Transaction received successfully.",
            "transaction_status_action": "ACCEPT",
            "transaction_status_reason": "VALID_TRANSACTION",
            "transaction_custom_sms": message
        }

    def _update_amounts(self, payment, amount, currency):
        order_payment = payment.order_payment
        order_payment.amount = Money(amount, currency)
        order_payment.save()

        donation = payment.order_payment.order.donations.first()
        donation.amount = Money(amount, currency)
        donation.save()

    def initiate_payment(self, data):
        """
        Documentation

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

        An actual (test) post

        api_key=c41a9c4986625499f30c1047e004d216
        api_signature=jtFAPZ7AO%2FMUz%2Bt8hzZ9LbX0uB1cXIDJj2upVKj6PauLbvMeu11N4J5q670W2YJ14NhdZEjrxIMnEQktQRGTzzAMJIWjQK%2FLztGIDHwavBf6Eyhmq8NrSiMswaNpeMFbS7oeHALPepWcPN9P3RXK3h5d3HygGkKiGQi9suGvEDI%3D
        api_version=1.0.4
        api_type=Initiate
        transaction_date=2017-10-28+18%3A42%3A46
        transaction_amount=1500
        transaction_type=Payment
        transaction_method=Paybill+%28M-Pesa%29
        transaction=7ACCB5CC8
        transaction_reference=7ACCB5CC8
        transaction_name=FRANCIS+JOAN+RACHEL
        transaction_mobile=31654631419
        transaction_paybill=961700
        transaction_paybill_type=Shared
        transaction_account=03858%231234
        transaction_account_number=03858
        transaction_merchant_reference=1234
        transaction_email=
        transaction_account_name=Primary
        transaction_code=7ACCB5CC8
        transaction_status=Completed
        transaction_country=KE
        transaction_currency=KES

        Response suggested by documentation
        http://developer.lipisha.com/index.php/app/launch/ipn_process_callback
        {
            "api_key": "3aa67677e8bf1d4c8fe886a38c03a860",
            "api_signature": "SYetmwsNnb5bwaZRyeQKhZNNkCoEx+5x=",
            "api_version": "2.0.0",
            "api_type": "Receipt",
            "transaction_reference": "CU79AW109",
            "transaction_status_code": "001",
            "transaction_status": "SUCCESS",
            "transaction_status_description": "Transaction received successfully.",
            "transaction_status_action": "ACCEPT",
            "transaction_status_reason": "VALID_TRANSACTION",
            "transaction_custom_sms": "Dear JOHN JANE DOE, your payment of KES 100.00 via CU79AW109D was received."
        }
        """
        account_number = data['transaction_account_number']
        transaction_merchant_reference = data['transaction_merchant_reference']
        transaction_reference = data['transaction_reference']
        payment = None

        # If account number has a # then it is a donation started at our platform
        if transaction_merchant_reference:
            try:
                order_payment = OrderPayment.objects.get(id=transaction_merchant_reference)
                if not order_payment.payment:
                    payment = LipishaPayment.objects.create(
                        order_payment=order_payment
                    )
                payment = order_payment.payment
                self._update_amounts(payment, data['transaction_amount'], data['transaction_currency'])
            except LipishaPayment.DoesNotExist:
                # Payment not found, probably not correctly filled in,
                # continue as an new anonymous donation
                pass

        if transaction_reference:
            try:
                payment = LipishaPayment.objects.get(transaction_reference=transaction_reference)
                return self.generate_response(payment)
            except LipishaPayment.DoesNotExist:
                # Payment not found, probably not correctly filled in,
                # continue as an new anonymous donation
                pass
            except LipishaPayment.MultipleObjectsReturned:
                # Multiple payments with that transaction_reference
                # FIXME: probably send a warning?
                payment = LipishaPayment.objects.filter(transaction_reference=transaction_reference).last()
                self._update_amounts(payment, data['transaction_amount'], data['transaction_currency'])

        if not payment:
            # If we haven't found a payment by now we should create one
            try:
                lipisha_project = LipishaProject.objects.get(account_number=account_number)
            except LipishaProject.DoesNotExist:
                raise PaymentException("Couldn't find a project for M-PESA payment.")

            order = Order.objects.create()
            name = data['transaction_name'].replace('+', ' ').title()

            Donation.objects.create(
                order=order,
                amount=Money(data['transaction_amount'], data['transaction_currency']),
                name=name,
                project=lipisha_project.project)
            order_payment = OrderPayment.objects.create(
                order=order,
                payment_method='lipishaMpesa'
            )
            payment = LipishaPayment.objects.create(
                order_payment=order_payment
            )

        payment.response = json.dumps(data)
        for k, v in data.items():
            setattr(payment, k, v)

        payment.transaction_mobile_number = data['transaction_mobile']
        payment.reference = data['transaction_mobile']

        if data['transaction_status'] == 'Completed':
            payment.status = 'settled'
            order_payment.settled()
        payment.reference = payment.order_payment_id
        payment.save()
        return self.generate_response(payment)
