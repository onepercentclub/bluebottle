# coding=utf-8
import logging
from django.contrib.sites.models import get_current_site
import gateway

from bluebottle.payments_docdata.models import DocdataTransaction
from django.utils.http import urlencode
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition, get_current_host
from .models import DocdataPayment
from .gateway import DocdataClient

logger = logging.getLogger(__name__)


class DocdataPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASS = DocdataPayment

    STATUS_MAPPING = {
        'NEW':                            StatusDefinition.STARTED,
        'STARTED':                        StatusDefinition.STARTED,
        'REDIRECTED_FOR_AUTHENTICATION':  StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZATION_REQUESTED':        StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZED':                     StatusDefinition.AUTHORIZED,
        'PAID':                           StatusDefinition.SETTLED, 
        'CANCELLED':                      StatusDefinition.CANCELLED,
        'CHARGED_BACK':                   StatusDefinition.CHARGED_BACK,
        'CONFIRMED_PAID':                 StatusDefinition.PAID,
        'CONFIRMED_CHARGEDBACK':          StatusDefinition.CHARGED_BACK,
        'CLOSED_SUCCESS':                 StatusDefinition.PAID,
        'CLOSED_CANCELLED':               StatusDefinition.CANCELLED,
    }

    def get_status_mapping(self, external_payment_status):
        return self.STATUS_MAPPING.get(external_payment_status)

    def create_payment(self):
        payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
        payment.total_gross_amount = self.order_payment.amount * 100

        testing_mode = settings.DOCDATA_SETTINGS['testing_mode']

        merchant = gateway.Merchant(name=settings.DOCDATA_MERCHANT_NAME, password=settings.DOCDATA_MERCHANT_PASSWORD)

        amount = gateway.Amount(value=self.order_payment.amount, currency='EUR')
        user = self.get_user_data()

        name = gateway.Name(
            first=user['first_name'],
            last=user['last_name']
        )

        shopper = gateway.Shopper(
            id=user['id'],
            name=name,
            email=user['email'],
            language='en',
            gender="U",
            date_of_birth=None,
            phone_number=None,
            mobile_phone_number=None,
            ipAddress=None)

        address = gateway.Address(
            street=u'Unknown',
            house_number='1',
            house_number_addition=u'',
            postal_code='Unknown',
            city=u'Unknown',
            state=u'',
            country_code='NL',
        )

        bill_to = gateway.Destination(name=name, address=address)

        client = gateway.DocdataClient(testing_mode)

        response = client.create(
            merchant=merchant,
            payment_id=self.order_payment.id,
            total_gross_amount=amount,
            shopper=shopper,
            bill_to=bill_to,
            description=_("Bluebottle donation"),
            receiptText=_("Bluebottle donation"),
            includeCosts=False,
            profile=settings.DOCDATA_SETTINGS['profile'],
            days_to_pay=settings.DOCDATA_SETTINGS['days_to_pay'],
            )

        payment.payment_cluster_key = response['order_key']
        payment.payment_cluster_id = response['order_id']
        payment.save()

        return payment

    def get_authorization_action(self):

        testing_mode = settings.DOCDATA_SETTINGS['testing_mode']

        client = gateway.DocdataClient(testing_mode)

        return_url_base = get_current_host()
        client_language = 'en'

        integration_data = self.order_payment.integration_data

        url = client.get_payment_menu_url(
            order_key=self.payment.payment_cluster_key,
            order_id=self.order_payment.order_id,
            return_url=return_url_base,
            client_language=client_language,
        )

        default_act = False
        if self.payment.ideal_issuer_id:
            default_act = True

        params = {
             'default_pm': self.payment.default_pm,
             'ideal_issuer_id': self.payment.ideal_issuer_id,
             'default_act': default_act
        }
        url += '&' + urlencode(params)
        return {'type': 'redirect', 'method': 'get', 'url': url}

    def check_payment_status(self):
        response = self._fetch_status()

        status = self.get_status_mapping(response.payment[0].authorization.status)
        if self.payment.status <> status:
            totals = response.approximateTotals
            self.payment.total_registered = totals.totalRegistered
            self.payment.total_shopper_pending = totals.totalShopperPending
            self.payment.total_acquirer_pending = totals.totalAcquirerPending
            self.payment.total_acquirer_approved = totals.totalAcquirerApproved
            self.payment.total_captured = totals.totalCaptured
            self.payment.total_refunded = totals.totalRefunded
            self.payment.total_charged_back = totals.totalChargedback

            self.payment.status = status
            self.payment.save()

        for transaction in response.payment:
            self._store_payment_transaction(transaction)

    def _store_payment_transaction(self, transaction):
        dd_transaction, created = DocdataTransaction.objects.get_or_create(docdata_id=transaction.id, payment=self.payment)
        dd_transaction.payment_method = transaction.paymentMethod
        dd_transaction.authorization_amount = transaction.authorization.amount.value
        dd_transaction.authorization_currency = transaction.authorization.amount._currency
        dd_transaction.authorization_status = transaction.authorization.status
        dd_transaction.capture_status = transaction.authorization.capture[0].status
        dd_transaction.capture_amount = transaction.authorization.capture[0].amount.value
        dd_transaction.capture_currency = transaction.authorization.capture[0].amount._currency
        dd_transaction.save()

    def _fetch_status(self):
        testing_mode = settings.DOCDATA_SETTINGS['testing_mode']
        client = gateway.DocdataClient(testing_mode)
        response = client.status(self.payment.payment_cluster_key)

        return response