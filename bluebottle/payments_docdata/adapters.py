import logging
import gateway

from django.utils.http import urlencode
from django.conf import settings

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
from bluebottle.payments_docdata.exceptions import (
    DocdataPaymentException, DocdataPaymentStatusException)
from bluebottle.payments_docdata.models import (
    DocdataTransaction, DocdataDirectdebitPayment)
from bluebottle.utils.utils import (StatusDefinition, get_current_host,
                                    get_client_ip)

from .models import DocdataPayment

logger = logging.getLogger('console')


class DocdataPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [DocdataPayment, DocdataDirectdebitPayment]

    # Payment methods specified by DocData. They should map to the payment
    # methods we specify in our settings file so we can map payment methods
    # of Docdata to our own definitions of payment methods
    PAYMENT_METHODS = {
        'MASTERCARD': 'docdataCreditcard',
        'VISA': 'docdataCreditcard',
        'MAESTRO': 'docdataCreditcard',
        'AMEX': 'docdataCreditcard',
        'IDEAL': 'docdataIdeal',
        'BANK_TRANSFER': 'docdataBanktransfer',
        'DIRECT_DEBIT': 'docdataDirectdebit',
        'SEPA_DIRECT_DEBIT': 'docdataDirectdebit'

    }

    def __init__(self, *args, **kwargs):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        super(DocdataPaymentAdapter, self).__init__(*args, **kwargs)

    def get_user_data(self):
        user = self.order_payment.order.user
        ip_address = get_client_ip()

        if user:
            user_data = {
                'id': user.id,
                'first_name': user.first_name or 'Unknown',
                'last_name': user.last_name or 'Unknown',
                'email': user.email,
                'ip_address': ip_address,
            }
        else:
            user_data = {
                'id': 1,
                'first_name': 'Nomen',
                'last_name': 'Nescio',
                'email': properties.CONTACT_EMAIL,
                'ip_address': ip_address
            }

        default_country_code = getattr(properties, 'DEFAULT_COUNTRY_CODE')

        if user and hasattr(user, 'address'):
            street = user.address.line1.split(' ')
            if street[-1] and any(char.isdigit() for char in street[-1]):
                user_data['house_number'] = street.pop(-1)
                if len(street):
                    user_data['street'] = ' '.join(street)
                else:
                    user_data['street'] = 'Unknown'
            else:
                user_data['house_number'] = 'Unknown'
                if user.address.line1:
                    user_data['street'] = user.address.line1
                else:
                    user_data['street'] = 'Unknown'

            if user.address.postal_code:
                user_data['postal_code'] = user.address.postal_code
            else:
                user_data['postal_code'] = 'Unknown'
            if user.address.city:
                user_data['city'] = user.address.city
            else:
                user_data['city'] = 'Unknown'
            if user.address.country and hasattr(user.address.country,
                                                'alpha2_code'):
                user_data['country'] = user.address.country.alpha2_code
            else:
                user_data['country'] = default_country_code
        else:
            user_data['postal_code'] = 'Unknown'
            user_data['street'] = 'Unknown'
            user_data['city'] = 'Unknown'
            user_data['country'] = default_country_code
            user_data['house_number'] = 'Unknown'

        if not user_data['country']:
            user_data['country'] = default_country_code

        user_data['company'] = ''
        user_data['kvk_number'] = ''
        user_data['vat_number'] = ''
        user_data['house_number_addition'] = ''
        user_data['state'] = ''

        return user_data

    def get_method_mapping(self, external_payment_method):
        return self.PAYMENT_METHODS.get(external_payment_method)

    def create_payment(self):
        if self.order_payment.payment_method == 'docdataDirectdebit':
            payment = DocdataDirectdebitPayment(
                order_payment=self.order_payment,
                **self.order_payment.card_data)
        else:
            payment = DocdataPayment(order_payment=self.order_payment,
                                     **self.order_payment.card_data)

        payment.total_gross_amount = self.order_payment.amount.amount * 100

        if payment.default_pm == 'paypal':
            payment.default_pm = 'paypal_express_checkout'

        merchant = gateway.Merchant(name=self.credentials['merchant_name'],
                                    password=self.credentials['merchant_password'])

        amount = gateway.Amount(value=self.order_payment.amount.amount, currency=self.order_payment.amount.currency)
        user = self.get_user_data()

        if payment.default_pm == 'ideal':
            # For ideal we fake the country to be NL
            user['country'] = 'NL'

        # Store user data on payment too
        payment.customer_id = user['id']
        payment.email = user['email']
        payment.first_name = user['first_name']
        payment.last_name = user['last_name']

        payment.address = user['street']
        # payment.street = user['street']
        # payment.house_number = user['house_number']

        payment.city = user['city']

        payment.country = user['country']
        # payment.ip_address = user['ip_address']

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
            ipAddress=user['ip_address'])

        address = gateway.Address(
            street=user['street'],
            house_number=user['house_number'],
            house_number_addition=user['house_number_addition'],
            postal_code=user['postal_code'],
            city=user['city'],
            state=user['state'],
            country_code=user['country'],
        )

        bill_to = gateway.Destination(name=name, address=address)

        client = gateway.DocdataClient(self.credentials, self.live_mode)

        info_text = self.order_payment.info_text

        response = client.create(
            merchant=merchant,
            payment_id=self.order_payment.id,
            total_gross_amount=amount,
            shopper=shopper,
            bill_to=bill_to,
            description=info_text,
            receiptText=info_text,
            includeCosts=False,
            profile=settings.DOCDATA_SETTINGS['profile'],
            days_to_pay=settings.DOCDATA_SETTINGS['days_to_pay'],
        )

        payment.payment_cluster_key = response['order_key']
        payment.payment_cluster_id = response['order_id']
        payment.save()

        return payment

    def get_authorization_action(self):

        client = gateway.DocdataClient(self.credentials, self.live_mode)

        # Get the language that the user marked as his / her primary language
        # or fallback on the default LANGUAGE_CODE in settings

        try:
            client_language = self.order_payment.order.user.primary_language
        except AttributeError:
            client_language = properties.LANGUAGE_CODE

        if self.order_payment.payment_method == 'docdataDirectdebit':
            try:
                client.start_remote_payment(
                    order_key=self.payment.payment_cluster_key,
                    payment=self.payment,
                    payment_method='SEPA_DIRECT_DEBIT'
                )
                return {'type': 'success'}
            except DocdataPaymentException as i:
                raise PaymentException(i)
        else:
            return_url_base = get_current_host()
        try:
            url = client.get_payment_menu_url(
                order_key=self.payment.payment_cluster_key,
                credentials=self.credentials,
                order_id=self.order_payment.order_id,
                return_url=return_url_base,
                client_language=client_language,
            )
        except DocdataPaymentException as i:
            raise PaymentException(i)

        default_act = False
        if self.payment.ideal_issuer_id:
            default_act = True
        if self.payment.default_pm == 'paypal_express_checkout':
            default_act = True

        url = client.get_payment_menu_url(
            order_key=self.payment.payment_cluster_key,
            order_id=self.order_payment.order_id,
            credentials=self.credentials,
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
        try:
            response = self._fetch_status()
        except DocdataPaymentStatusException, e:
            if 'REQUEST_DATA_INCORRECT' == e.message and 'Order could not be found' in e.report_type:
                # The payment was not found in docdata: Mark the payment as failed
                logger.error(
                    'Fetching status failed for payment {0}: {1}'.format(
                        self.payment.id, e))
                self.payment.status = StatusDefinition.FAILED
                self.payment.save()
                return None
            else:
                raise

        # Only continue this if there's a payment set.
        if not hasattr(response, 'payment'):
            return None

        totals = response.approximateTotals

        if int(totals.totalAcquirerApproved) + int(
                totals.totalAcquirerPending) + int(
                totals.totalShopperPending) + int(totals.totalCaptured) == 0:
            # No payment has been authorized
            statuses = {payment.authorization.status for payment in
                        response.payment}

            if {'NEW', 'STARTED', 'REDIRECTED_FOR_AUTHORIZATION',
                    'AUTHORIZATION_REQUESTED', 'AUTHENTICATED', 'RISK_CHECK_OK',
                    'AUTHORIZED'} & statuses:
                # All these statuses belong are considered new
                status = StatusDefinition.STARTED
            elif statuses == {'CANCELED', }:
                # If all of them are cancelled, the whole payment is cancelled
                # Yes, docdata uses "CANCELED"
                status = StatusDefinition.CANCELLED
            elif {'RISK_CHECK_FAILED', 'AUTHORIZATION_ERROR',
                  'AUTHORIZATION_FAILED'} & statuses:
                # If all of them are cancelled, the whole payment is cancelled
                # Yes, docdata uses "CANCELED"
                status = StatusDefinition.FAILED
            else:
                status = StatusDefinition.UNKNOWN
        else:
            # We have some authorized payments
            if int(totals.totalChargedback) == int(totals.totalRegistered):
                # Everything is charged back
                status = StatusDefinition.CHARGED_BACK
            elif int(totals.totalChargedback) + int(
                    totals.totalRefunded) == int(totals.totalRegistered):
                # Everything is refunded (even if it was partially charged back
                status = StatusDefinition.REFUNDED
            elif int(totals.totalCaptured) == int(totals.totalRegistered):
                # Everything was captured
                status = StatusDefinition.SETTLED
            elif int(totals.totalAcquirerApproved) + int(
                    totals.totalAcquirerPending) + int(
                    totals.totalShopperPending) == int(totals.totalRegistered):
                # Everything was authorized
                status = StatusDefinition.AUTHORIZED
            else:
                # Anything else (Partly captured, partly charged back, etc)
                status = StatusDefinition.UNKNOWN

        if self.payment.status != status:
            self.payment.total_registered = totals.totalRegistered
            self.payment.total_shopper_pending = totals.totalShopperPending
            self.payment.total_acquirer_pending = totals.totalAcquirerPending
            self.payment.total_acquirer_approved = totals.totalAcquirerApproved
            self.payment.total_captured = totals.totalCaptured
            self.payment.total_refunded = totals.totalRefunded
            self.payment.total_charged_back = totals.totalChargedback
            self.payment.status = status

            try:
                payment_method = [
                    payment.authorization.paymentMethod
                    for payment in response.payment
                    if payment.authorization.method == 'AUTHORIZED'][0]
            except (AttributeError, IndexError):
                payment_method = None

            if payment_method:
                self.payment.default_pm = payment_method
                self.order_payment.payment_method = self.get_method_mapping(
                    payment_method)
                self.order_payment.save()
            self.payment.save()

        for transaction in response.payment:
            self._store_payment_transaction(transaction)

    def refund_payment(self):
        client = gateway.DocdataClient(self.credentials, self.live_mode)

        logger.warn(
            'Attempting to refund payment {0}.'.format(self.payment.id)
        )

        client.refund(
            self.order_payment.payment.payment_cluster_key,
        )

    def _store_payment_transaction(self, transaction):
        dd_transaction, _created = DocdataTransaction.objects.get_or_create(
            docdata_id=transaction.id, payment=self.payment
        )

        dd_transaction.payment_method = transaction.paymentMethod
        dd_transaction.authorization_amount = transaction.authorization.amount.value
        dd_transaction.authorization_currency = transaction.authorization.amount._currency
        dd_transaction.authorization_status = transaction.authorization.status
        dd_transaction.raw_response = str(transaction)

        if hasattr(transaction.authorization, 'capture'):
            dd_transaction.capture_amount = sum(
                int(capture.amount.value) for capture in
                transaction.authorization.capture)
            dd_transaction.capture_status = transaction.authorization.capture[
                0].status
            dd_transaction.capture_currency = transaction.authorization.capture[
                0].amount._currency

        if hasattr(transaction.authorization, 'chargeback'):
            dd_transaction.chargeback_amount = sum(
                int(chargeback.amount.value) for chargeback in
                transaction.authorization.chargeback)

        if hasattr(transaction.authorization, 'refund'):
            dd_transaction.refund_amount = sum(
                int(refund.amount.value) for refund in
                transaction.authorization.refund)

        dd_transaction.save()

    def _fetch_status(self):
        client = gateway.DocdataClient(self.credentials, self.live_mode)
        response = client.status(self.payment.payment_cluster_key)

        return response
