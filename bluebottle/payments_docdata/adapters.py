import logging
from bluebottle.payments_logger.models import PaymentLogEntry
import gateway

from django.utils.http import urlencode
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from bluebottle.payments.exception import PaymentException
from bluebottle.payments_docdata.exceptions import DocdataPaymentException
from bluebottle.payments_docdata.models import DocdataTransaction, DocdataDirectdebitPayment
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition, get_current_host, get_client_ip, get_country_code_by_ip
from .models import DocdataPayment
from bluebottle.clients import properties


logger = logging.getLogger(__name__)


class DocdataPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [DocdataPayment, DocdataDirectdebitPayment]

    # Payment methods specified by DocData. They should map to the payment methods we specify in our settings file so we can map
    # payment methods of Docdata to our own definitions of payment methods
    PAYMENT_METHODS = {
        'MASTERCARD'                        : 'docdataCreditcard',
        'VISA'                              : 'docdataCreditcard',
        'MAESTRO'                           : 'docdataCreditcard',
        'AMEX'                              : 'docdataCreditcard',
        'IDEAL'                             : 'docdataIdeal',
        'BANK_TRANSFER'                     : 'docdataBanktransfer',
        'DIRECT_DEBIT'                      : 'docdataDirectdebit',
        'SEPA_DIRECT_DEBIT'                 : 'docdataDirectdebit'

    }

    STATUS_MAPPING = {
        'NEW':                            StatusDefinition.STARTED,
        'STARTED':                        StatusDefinition.STARTED,
        'REDIRECTED_FOR_AUTHENTICATION':  StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZATION_REQUESTED':        StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZED':                     StatusDefinition.AUTHORIZED,
        'PAID':                           StatusDefinition.SETTLED,
        'CANCELED':                       StatusDefinition.CANCELLED, # Docdata responds with 'CANCELED'
        'CHARGED_BACK':                   StatusDefinition.CHARGED_BACK,
        'CONFIRMED_PAID':                 StatusDefinition.SETTLED,
        'CONFIRMED_CHARGEDBACK':          StatusDefinition.CHARGED_BACK,
        'CLOSED_SUCCESS':                 StatusDefinition.SETTLED,
        'CLOSED_CANCELLED':               StatusDefinition.CANCELLED,
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
                street_name = ' '.join(street)
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
            if user.address.country and hasattr(user.address.country, 'alpha2_code'):
                user_data['country'] = user.address.country.alpha2_code
            elif get_country_code_by_ip(ip_address):
                user_data['country'] = get_country_code_by_ip(ip_address)
            else:
                user_data['country'] = default_country_code
        else:
            user_data['postal_code'] = 'Unknown'
            user_data['street'] = 'Unknown'
            user_data['city'] = 'Unknown'
            country = get_country_code_by_ip(ip_address)
            if country:
                user_data['country'] = country
            else:
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


    def get_status_mapping(self, external_payment_status):
        return self.STATUS_MAPPING.get(external_payment_status)

    def create_payment(self):
        if self.order_payment.payment_method == 'docdataDirectdebit':
            payment = DocdataDirectdebitPayment(order_payment=self.order_payment, **self.order_payment.integration_data)
        else:
            payment = DocdataPayment(order_payment=self.order_payment, **self.order_payment.integration_data)

        payment.total_gross_amount = self.order_payment.amount * 100

        if payment.default_pm == 'paypal':
            payment.default_pm = 'paypal_express_checkout'

        merchant = gateway.Merchant(name=properties.DOCDATA_MERCHANT_NAME, password=properties.DOCDATA_MERCHANT_PASSWORD)

        amount = gateway.Amount(value=self.order_payment.amount, currency='EUR')
        user = self.get_user_data()

        # Store user data on payment too
        payment.customer_id = user['id']
        payment.email = user['email']
        payment.first_name = user['first_name']
        payment.last_name = user['last_name']

        payment.address = user['street']
        # payment.street = user['street']
        # payment.house_number = user['house_number']

        payment.city = user['city']

        # payment.country = user['country']
        # payment. = user['ip_address']

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

        client = gateway.DocdataClient(self.live_mode)

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

        client = gateway.DocdataClient(self.live_mode)

        # Get the language that the user marked as his / her primary language
        # or fallback on the default LANGUAGE_CODE in settings

        try:
            client_language = self.order_payment.order.user.primary_language
        except AttributeError:
            client_language = properties.LANGUAGE_CODE

        if self.order_payment.payment_method == 'docdataDirectdebit':
            try:
                reply = client.start_remote_payment(
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
                order_id=self.order_payment.order_id,
                return_url=return_url_base,
                client_language=client_language,
            )
        except DocdataPaymentException as i:
            raise PaymentException(i)

        integration_data = self.order_payment.integration_data
        default_act = False
        if self.payment.ideal_issuer_id:
            default_act = True
        if self.payment.default_pm == 'paypal_express_checkout':
            default_act = True

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

        # Only continue this if there's a payment set.
        if not hasattr(response, 'payment'):
            return None

        status = self.get_status_mapping(response.payment[0].authorization.status)

        totals = response.approximateTotals
        if totals.totalCaptured - totals.totalChargedback - totals.totalChargedback > 0:
            status = StatusDefinition.SETTLED

        if self.payment.status <> status:
            self.payment.total_registered = totals.totalRegistered
            self.payment.total_shopper_pending = totals.totalShopperPending
            self.payment.total_acquirer_pending = totals.totalAcquirerPending
            self.payment.total_acquirer_approved = totals.totalAcquirerApproved
            self.payment.total_captured = totals.totalCaptured
            self.payment.total_refunded = totals.totalRefunded
            self.payment.total_charged_back = totals.totalChargedback
            self.payment.status = status
            self.payment.save()

        # FIXME: Saving transactions fails...
        # for transaction in response.payment:
        #    self._store_payment_transaction(transaction)

    def _store_payment_transaction(self, transaction):
        dd_transaction, created = DocdataTransaction.objects.get_or_create(docdata_id=transaction.id, payment=self.payment)
        dd_transaction.payment_method = transaction.paymentMethod
        dd_transaction.authorization_amount = transaction.authorization.amount.value
        dd_transaction.authorization_currency = transaction.authorization.amount._currency
        dd_transaction.authorization_status = transaction.authorization.status
        if hasattr(transaction.authorization, 'capture'):
            dd_transaction.capture_status = transaction.authorization.capture[0].status
            dd_transaction.capture_amount = transaction.authorization.capture[0].amount.value
            dd_transaction.capture_currency = transaction.authorization.capture[0].amount._currency

        dd_transaction.save()

    def _fetch_status(self):
        client = gateway.DocdataClient(self.live_mode)
        response = client.status(self.payment.payment_cluster_key)

        return response
