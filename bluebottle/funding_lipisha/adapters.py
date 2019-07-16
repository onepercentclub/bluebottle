# coding=utf-8
import json
import logging

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

logger = logging.getLogger()


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

        try:
            account_number = response['content']['transaction_account_number']

            LipishaProject.objects.create(
                project=project,
                account_number=account_number
            )
        except KeyError:
            raise PaymentException("Could not create an account number at Lipisha")

    def generate_success_response(self, payment):
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
            "api_type": "Receipt",
            "transaction_reference": payment.transaction_reference,
            "transaction_status_code": "001",
            "transaction_status": "SUCCESS",
            "transaction_status_description": "Transaction received successfully.",
            "transaction_status_action": "ACCEPT",
            "transaction_status_reason": "VALID_TRANSACTION",
            "transaction_custom_sms": message
        }

    def generate_error_response(self, reference):
        return {
            "api_key": self.credentials['api_key'],
            "api_signature": self.credentials['api_signature'],
            "api_version": "1.0.4",
            "api_type": "Receipt",
            "transaction_reference": reference,
            "transaction_status_code": "002",
            "transaction_status": "FAIL",
            "transaction_status_description": "Transaction has a problem and we reject.",
            "transaction_status_action": "REJECT",
            "transaction_status_reason": "INVALID_TRANSACTION"
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
        Look for an existing payment and update that or create a new one.
        """
        account_number = data['transaction_account_number']
        transaction_merchant_reference = data['transaction_merchant_reference']
        transaction_reference = data['transaction_reference']
        payment = None
        order_payment = None

        # Credentials should match
        if self.credentials['api_key'] != data['api_key']:
            return self.generate_error_response(transaction_reference)
        if self.credentials['api_signature'] != data['api_signature']:
            return self.generate_error_response(transaction_reference)

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
            except OrderPayment.DoesNotExist:
                # Payment not found, probably not correctly filled in,
                # continue as an new anonymous donation
                pass

        if transaction_reference:
            try:
                payment = LipishaPayment.objects.get(transaction_reference=transaction_reference)
                order_payment = payment.order_payment
            except LipishaPayment.DoesNotExist:
                # Payment not found, probably not correctly filled in,
                # continue as an new anonymous donation
                pass
            except LipishaPayment.MultipleObjectsReturned:
                # Multiple payments with that transaction_reference
                # FIXME: probably send a warning?
                payment = LipishaPayment.objects.filter(transaction_reference=transaction_reference).last()
                order_payment = payment.order_payment
                self._update_amounts(payment, data['transaction_amount'], data['transaction_currency'])

        if not payment:
            # If we haven't found a payment by now we should create one
            try:
                lipisha_project = LipishaProject.objects.get(account_number=account_number)
            except LipishaProject.DoesNotExist:
                logger.error("Couldn't find a project for M-PESA payment {}".format(account_number))
                return self.generate_error_response(transaction_reference)

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
            try:
                setattr(payment, k, v)
            except AttributeError:
                pass

        payment.transaction_mobile_number = data['transaction_mobile']
        payment.reference = data['transaction_mobile']

        if data['transaction_status'] == 'Completed':
            payment.status = 'authorized'
            order_payment.authorized()
        else:
            payment.status = 'failed'
            order_payment.failed()
        payment.reference = payment.order_payment_id
        payment.save()
        return self.generate_success_response(payment)

    def acknowledge_payment(self, data):
        """
        Find existing payment and switch to given status
        """
        transaction_reference = data['transaction_reference']

        # Credentials should match
        if self.credentials['api_key'] != data['api_key']:
            return self.generate_error_response(transaction_reference)
        if self.credentials['api_signature'] != data['api_signature']:
            return self.generate_error_response(transaction_reference)

        try:
            payment = LipishaPayment.objects.get(transaction_reference=transaction_reference)
        except LipishaPayment.DoesNotExist:
            return self.generate_error_response(transaction_reference)
        except LipishaPayment.MultipleObjectsReturned:
            payment = LipishaPayment.objects.filter(transaction_reference=transaction_reference).last()

        payment.response = json.dumps(data)
        for k, v in data.items():
            try:
                setattr(payment, k, v)
            except AttributeError:
                pass

        payment.transaction_mobile_number = data['transaction_mobile']
        payment.reference = data['transaction_mobile']
        order_payment = payment.order_payment

        if data['transaction_status'] == 'Success':
            payment.status = 'settled'
            order_payment.settled()
        else:
            payment.status = 'failed'
            order_payment.failed()
        payment.reference = payment.order_payment_id
        payment.save()
        return self.generate_success_response(payment)
