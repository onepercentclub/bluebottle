# coding=utf-8
import json
import logging

from lipisha import Lipisha, lipisha
from moneyed.classes import Money

from bluebottle.clients import properties
from bluebottle.donations.models import Donation
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.orders.models import Order
from bluebottle.payments.models import OrderPayment
from bluebottle.payments_lipisha.models import LipishaProject
from .models import LipishaPayment

logger = logging.getLogger()


class LipishaPaymentInterface(object):
    credentials = {}

    def __init__(self):
        provider = LipishaPaymentProvider.objects.get()
        self.credentials = provider.private_settings

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
        donation = payment.donation
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

        payment.mobile_number = data['transaction_mobile']

        if data['transaction_status'] == 'Success':
            payment.succeed()
        else:
            payment.fail()
        payment.save()
        return self.generate_success_response(payment)
