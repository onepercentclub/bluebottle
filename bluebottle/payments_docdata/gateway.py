"""
Backend calls to docdata.

Thanks to https://github.com/edoburu/django-oscar-docdata for extending our original implementation
which is Apache licensed, copyright (c) 2013 Diederik van der Boor

"""
import logging
import unicodedata

from django.utils.translation import get_language

from suds.client import Client
from suds import plugin
from urllib import urlencode
from urllib2 import URLError

from bluebottle.payments_docdata.exceptions import DocdataPaymentException

from .exceptions import DocdataPaymentStatusException

logger = logging.getLogger()

__all__ = (
    'DocdataClient',

    'CreateReply',
    'StartReply',
    'StatusReply',

    'Name',
    'Shopper',
    'Destination',
    'Address',
    'Amount',

    'Payment',
    'AmexPayment',
    'MasterCardPayment',
    'DirectDebitPayment',
    'IdealPayment',
    'BankTransferPayment',
    'ElvPayment',
)


def get_suds_client(live_mode=False):
    """
    Create the suds client to connect to docdata.
    """
    if live_mode:
        url = 'https://secure.docdatapayments.com/ps/services/paymentservice/1_2?wsdl'
    else:
        url = 'https://test.docdatapayments.com/ps/services/paymentservice/1_2?wsdl'

    # TODO: CACHE THIS object, avoid having to request the WSDL at every instance.
    try:
        return Client(url, plugins=[DocdataAPIVersionPlugin()])
    except URLError as e:
        logger.error('{0} {1}'.format(
            "Could not initialize SUDS SOAP client to connect to Docdata",
            str(e)))
        raise


class DocdataAPIVersionPlugin(plugin.MessagePlugin):
    """
    This adds the API version number to the body element. This is required
    for the Docdata soap API.
    """

    def marshalled(self, context):
        body = context.envelope.getChild('Body')
        request = body[0]
        request.set('version', '1.2')


class DocdataClient(object):
    """
    API Client for docdata.

    This is a wrapper around the SOAP service methods,
    providing more Python-friendly wrappers.
    """

    # Payment methods for the start operation.
    PAYMENT_METHOD_AMEX = 'AMEX'
    PAYMENT_METHOD_MASTERCARD = 'MASTERCARD'
    PAYMENT_METHOD_VISA = 'VISA'
    PAYMENT_METHOD_DIRECT_DEBIT = 'DIRECT_DEBIT'
    PAYMENT_METHOD_BANK_TRANSFER = 'BANK_TRANSFER'
    PAYMENT_METHOD_ELV = 'ELV'

    def __init__(self, credentials, live_mode=False):
        """
        Initialize the client.
        """

        self.client = get_suds_client(live_mode)
        self.live_mode = live_mode

        # Create the merchant node which is passed to every request.
        # The _ notation is used to assign attributes to the XML node,
        # instead of child elements.
        self.merchant = self.client.factory.create('ns0:merchant')
        self.merchant._name = credentials['merchant_name']
        self.merchant._password = credentials['merchant_password']

        # Create the integration info node which is passed to every request.
        self.integration_info = TechnicalIntegrationInfo()

    def create(self, merchant, payment_id, total_gross_amount, shopper, bill_to,
               description, receiptText=None,
               includeCosts=False, profile='webmenu', days_to_pay=7):
        """
        Create the payment in docdata.

        This is the first step of any payment session.
        After the payment is created, an ``order_key`` will be used.
        This key can be used to continue using the Payment Menu,
        or make the next call to start a Web Direct payment.

        The goal of the create operation is solely to create a payment order
        on Docdata Payments system.
        Creating a payment order is always the first step of any workflow in
        Docdata Payments payment service.

        After an order is created, payments can be made on this order; either
        through (the shopper via) the web menu or through the API by the
        merchant. If the order has been created using information on specific
        order items, the web menu can make use of this information by
        displaying a shopping cart.

        :param order_id: Unique merchant reference to this order.
        :type total_gross_amount: Amount
        :param shopper: Information concerning the shopper who placed the order.
        :type shopper: Shopper
        :param bill_to: Name and address to use for billing.
        :type bill_to: Destination
        :param description: The description of the order (max 50 chars).
        :type description: str
        :param receiptText: The description that is used by payment providers
        on shopper statements (max 50 chars).
        :type receiptText: str
        :param profile: The profile that is used to select the payment methods
        that can be used to pay this order.
        :param days_to_pay: The expected number of days in which the payment
        should be processed, or be expired if not paid.
        :rtype: CreateReply
        """
        # Preferences for the DocData system.
        paymentPreferences = self.client.factory.create(
            'ns0:paymentPreferences')
        paymentPreferences.profile = profile
        paymentPreferences.numberOfDaysToPay = days_to_pay
        # paymentPreferences.exhortation.period1 ?
        # paymentPreferences.exhortation.period2 ?

        # Menu preferences are empty. They are used for CSS file selection in
        # the payment menu.
        menuPreferences = self.client.factory.create('ns0:menuPreferences')

        # Execute create payment order request.
        #
        # create(
        #     merchant merchant, string35 merchantOrderReference,
        #     paymentPreferences paymentPreferences,
        #     menuPreferences menuPreferences, shopper shopper, amount
        #     totalGrossAmount, destination billTo, string50 description,
        #     string50 receiptText, xs:boolean includeCosts,
        #     paymentRequest paymentRequest, invoice invoice )
        #
        # The WSDL and XSD also contain documentation individualnvidual parameters:
        # https://secure.docdatapayments.com/ps/services/paymentservice/1_0?xsd=1
        #
        # TODO: can also pass shipTo + invoice details to docdata.
        # This displays the results in the docdata web menu.
        #
        done = False
        t = 1

        while not done:
            merchant_order_reference = "{0}-{1}".format(payment_id, t)

            reply = self.client.service.create(
                merchant=merchant.to_xml(self.client.factory),
                merchantOrderReference=merchant_order_reference,
                paymentPreferences=paymentPreferences,
                menuPreferences=menuPreferences,
                shopper=shopper.to_xml(self.client.factory),
                totalGrossAmount=total_gross_amount.to_xml(self.client.factory),
                billTo=bill_to.to_xml(self.client.factory),
                description=description,
                receiptText=receiptText or None,
                includeCosts=includeCosts or False,
                integrationInfo=self.integration_info.to_xml(
                    self.client.factory)
            )
            if hasattr(reply, 'createSuccess'):
                done = True
                order_key = str(reply['createSuccess']['key'])

            elif hasattr(reply, 'createError'):
                if reply.createError.error.value == "Merchant order reference is not unique.":
                    t += 1
                else:
                    error = reply.createError.error
                    message = error.value
                    message = message.replace(
                        "XML request does not match XSD. The data is: cvc-type.3.1.3: ",
                        "")

                    # log_docdata_error(error, message)
                    raise DocdataPaymentException(message, error._code)
            else:
                raise DocdataPaymentException(
                    'Received unknown reply from DocData. Remote Payment not created.')

        return {'order_id': merchant_order_reference, 'order_key': order_key}

    def start_remote_payment(self, order_key, payment=None,
                             payment_method='SEPA_DIRECT_DEBIT', **extra_args):
        """
        The start operation is used for starting a (web direct) payment on an order.
        It does not need to be used if the merchant makes use of Docdata Payments web menu.

        The web direct can be used for direct debit for example.
        Standard payments (e.g. iDEAL, creditcard) all happen through the web menu
        because implementing those locally requires certification by the credit card companies.
        """
        if not order_key:
            raise DocdataPaymentException("Missing order_key!")

        paymentRequestInput = self.client.factory.create('ns0:paymentRequestInput')

        # We only need to set amount because of bug in suds library. Otherwise
        # it defaults to order amount.
        paymentAmount = self.client.factory.create('ns0:amount')
        paymentAmount.value = str(int(payment.total_gross_amount))
        paymentAmount._currency = 'EUR'
        paymentRequestInput.paymentAmount = paymentAmount

        if payment_method == 'SEPA_DIRECT_DEBIT':
            paymentRequestInput.paymentMethod = 'SEPA_DIRECT_DEBIT'
            PaymentInput = DirectDebitPayment(
                holder_name=self.convert_to_ascii(payment.account_name),
                holder_city=self.convert_to_ascii(payment.account_city),
                holder_country_code='NL',
                bic=payment.bic, iban=payment.iban)

            paymentRequestInput.directDebitPaymentInput = PaymentInput.to_xml(
                self.client.factory)

        if payment_method == 'MASTERCARD':
            paymentRequestInput.paymentMethod = 'MASTERCARD'
            PaymentInput = MasterCardPayment(credit_card_number=None,
                                             expiry_date=None,
                                             cvc2=None,
                                             card_holder=None,
                                             email_address=None)

        # Execute start payment request.
        reply = self.client.service.start(self.merchant, order_key,
                                          paymentRequestInput)

        if hasattr(reply, 'startSuccess'):
            return str(reply['startSuccess']['paymentId'])
        elif hasattr(reply, 'startError'):
            error = reply['startError']['error']
            error_message = "{0} {1}".format(error['_code'], error['value'])
            logger.error(error_message)
            raise DocdataPaymentException(error['value'])

        else:
            error_message = 'Received unknown reply from DocData. WebDirect payment not created.'
            logger.error(error_message)
            raise DocdataPaymentException(error_message)

    def status(self, order_key):
        """
        Request the status of of order and it's payments.
        """
        if not order_key:
            raise DocdataPaymentException("Missing order_key!")

        reply = self.client.service.status(
            self.merchant,
            order_key,
            iIntegrationInfo=self.integration_info.to_xml(self.client.factory)
        )

        if hasattr(reply, 'statusSuccess'):
            return reply.statusSuccess.report
        elif hasattr(reply, 'statusError'):
            error = reply.statusError.error
            # FIXME Log ERROR here
            raise DocdataPaymentStatusException(error._code, error.value)
        else:
            logger.error("Unexpected response node from docdata!")
            # FIXME Log ERROR here
            raise NotImplementedError(
                'Received unknown reply from DocData. No status processed from Docdata.')

    def get_payment_menu_url(self, order_key, order_id, credentials, return_url=None,
                             client_language=None, **extra_url_args):
        """
        Return the URL to the payment menu,
        where the user can be redirected to after creating a successful payment.

        Make sure URLs are absolute, and include the hostname
        and ``https://`` part.

        When using default_act (possible values "yes" or "true") as well as
        default_pm, your shopper will be redirected straight from your shop to
        the payment page of the payment method.
        This works only with those payment methods that are initiated by a
        single click, PayPal, Rabo SMS-betalen, SofortUberweisung, eBanking,
        KBC Betaalknop and iDEAL.
        When the issuer_id is added to the redirect string, this works for
        iDEAL as well.

        :param extra_args: Additional URL arguments, e.g. default_pm=IDEAL,
        ideal_issuer_id=0021, default_act='true'
        """

        # We should not use the 'go' link. When we get redirected back from
        # docdata the redirects app, at that point, has no notion of the
        # language of the user and defaults to english. This breaks in Safari.
        # However, we do not need the 'redirects' app here because we know the
        # language and we can generate the exact link.
        args = {
            'command': 'show_payment_cluster',
            'payment_cluster_key': order_key,
            'merchant_name': credentials['merchant_name'],
            'return_url_success': "{0}/{1}/orders/{2}/success".format(
                return_url, client_language, order_id),
            'return_url_pending': "{0}/{1}/orders/{2}/pending".format(
                return_url, client_language, order_id),
            'return_url_canceled': "{0}/{1}/orders/{2}/cancelled".format(
                return_url, client_language, order_id),
            'return_url_error': "{0}/{1}/orders/{2}/error".format(return_url,
                                                                  client_language,
                                                                  order_id),
            'client_language': (client_language or get_language()).upper()
        }
        args.update(extra_url_args)

        if self.live_mode:
            return 'https://secure.docdatapayments.com/ps/menu?' + urlencode(
                args)
        else:
            return 'https://test.docdatapayments.com/ps/menu?' + urlencode(args)

    def convert_to_ascii(self, value):
        """ Normalize / convert unicode characters to ascii equivalents. """
        if isinstance(value, unicode):
            return unicodedata.normalize('NFKD', value).encode('ascii',
                                                               'ignore')
        else:
            return value


class CreateReply(object):
    """
    Docdata response for the create request
    """

    def __init__(self, order_id, order_key):
        # In this library, we favor explicit reply objects over dictionaries,
        # because it makes it much more explicit what is being returned.
        # BTW, PyPy also loves this ;) Much easier to optimize then dict lookups.
        self.order_id = order_id
        self.order_key = order_key

    def __repr__(self):
        return "<CreateReply {0}>".format(self.order_key)


class StartReply(object):
    """
    Docdata response for the start request.
    """

    def __init__(self, payment_id):
        self.payment_id = payment_id

    def __repr__(self):
        return "<StartReply {0}>".format(self.payment_id)


class StatusReply(object):
    """
    Docdata response for the status request.
    """

    def __init__(self, order_key, report):
        self.order_key = order_key
        self.report = report

    def __repr__(self):
        return "<StatusReply {0}>".format(repr(self.report))


class Merchant(object):
    """
    An merchant for Docdata.
    """

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def to_xml(self, factory):
        node = factory.create('ns0:merchant')
        node._name = self.name
        node._password = self.password
        return node


class Name(object):
    """
    A name for Docdata.

    :type first: unicode
    :type last: unicode
    :type middle: unicode
    :type initials: unicode
    :type prefix: unicode
    :type suffix: unicode
    """

    def __init__(self, first, last, middle=None, initials=None, prefix=None,
                 suffix=None):
        if not last:
            raise DocdataPaymentException("Last name is required!")
        if not first:
            raise DocdataPaymentException("First name is required!")
        self.first = first
        self.last = last
        self.prefix = prefix
        self.initials = initials
        self.middle = middle
        self.suffix = suffix

    def to_xml(self, factory):
        # Assigning values is perhaps very Java-esque, but it's very obvious too
        # what's happening here, while keeping Python-like constructor argument styles.
        node = factory.create('ns0:name')
        node.first = unicode(self.first)
        node.middle = unicode(self.middle) if self.middle else None
        node.last = unicode(self.last)
        node.initials = unicode(self.initials) if self.initials else None
        node.prefix = unicode(self.prefix) if self.prefix else None
        node.suffix = unicode(self.suffix) if self.suffix else None
        return node


class Shopper(object):
    """
    Information concerning the shopper who placed the order.

    :type id: long
    :type name: Name
    :type email: str
    :type language: str
    :type gender: str
    :type date_of_birth: :class:`datetime.Date`
    :type phone_number: str
    :type mobile_phone_number: str
    """

    def __init__(self, id, name, email, language, gender="U",
                 date_of_birth=None, phone_number=None,
                 mobile_phone_number=None, ipAddress=None):
        """
        :type name: Name
        """
        self.id = id
        self.name = name
        self.email = email
        self.language = language
        self.gender = gender  # M (male), F (female), U (undefined)
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.mobile_phone_number = mobile_phone_number  # +316..
        self.ipAddress = ipAddress

    def to_xml(self, factory):
        language_node = factory.create('ns0:language')
        language_node._code = self.language

        node = factory.create('ns0:shopper')
        node._id = self.id  # attribute, hence the ._id
        node.name = self.name.to_xml(factory)
        node.gender = self.gender.upper() if self.gender else "U"
        node.language = language_node
        node.email = self.email
        node.dateOfBirth = self.date_of_birth.isoformat() if self.date_of_birth else None  # yyyy-mm-dd
        node.phoneNumber = self.phone_number  # string50, must start with "+"
        node.mobilePhoneNumber = self.mobile_phone_number  # string50, must start with "+"
        node.ipAddress = self.ipAddress if self.ipAddress else None
        return node


class Destination(object):
    """
    Name and address to use for billing.
    """

    def __init__(self, name, address):
        """
        :type name: Name
        :type address: Address
        """
        self.name = name
        self.address = address

    def to_xml(self, factory):
        node = factory.create('ns0:destination')
        node.name = self.name.to_xml(factory)
        node.address = self.address.to_xml(factory)
        return node


class Address(object):
    """
    An address for docdata

    :type street: unicode
    :type house_number: str
    :type house_number_addition: unicode
    :type postal_code: str
    :type city: unicode
    :type state: unicode
    :type country_code: str
    :type company: unicode
    :type vatNumber: unicode
    :type careOf: unicode
    """

    def __init__(self, street, house_number, house_number_addition, postal_code,
                 city, state, country_code, company=None, vatNumber=None,
                 careOf=None):
        self.street = street
        self.house_number = house_number
        self.house_number_addition = house_number_addition
        self.postal_code = postal_code
        self.city = city
        self.state = state
        self.country_code = country_code

        self.company = company
        self.vatNumber = vatNumber
        self.careOf = careOf
        # self.kvkNummer    # rant: seriously? a Netherlands-specific field in the API?

    def to_xml(self, factory):
        country = factory.create('ns0:country')
        country._code = unicode(self.country_code)

        node = factory.create('ns0:address')
        node.street = unicode(self.street)
        node.houseNumber = unicode(self.house_number)  # string35
        node.houseNumberAddition = unicode(
            self.house_number_addition) if self.house_number_addition else None
        # Spaces aren't allowed in the Docdata postal code (type=NMTOKEN)
        node.postalCode = unicode(self.postal_code.replace(' ', ''))
        node.city = unicode(self.city)
        node.state = unicode(self.state) if self.state else None
        node.country = country

        # Optional company info
        node.company = unicode(self.company) if self.company else None
        node.vatNumber = unicode(self.vatNumber) if self.vatNumber else None
        node.careOf = unicode(self.careOf) if self.careOf else None
        return node


class Amount(object):
    """
    An amount for Docdata.
    """

    def __init__(self, value, currency):
        self.value = value
        self.currency = currency

    def to_xml(self, factory):
        node = factory.create('ns0:amount')
        node.value = int(self.value * 100)  # No comma!
        node._currency = self.currency  # An attribute
        return node


class TechnicalIntegrationInfo(object):
    """
    Pass integration information to the API for debugging assistance.
    """

    def to_xml(self, factory):
        node = factory.create('ns0:technicalIntegrationInfo')
        node.webshopPlugin = "bluebottle-docdata"
        node.webshopPluginVersion = "0.0.1"
        node.programmingLanguage = "Python"
        return node


class Payment(object):
    """
    Base interface for all payment inputs.
    """
    payment_method = None
    request_parameter = None

    def to_xml(self, factory):
        raise NotImplementedError(
            "Missing to_xml() implementation in {0}".format(
                self.__class__.__name__))


class AmexPayment(Payment):
    """
    American Express payment.
    """
    payment_method = DocdataClient.PAYMENT_METHOD_AMEX
    request_parameter = 'amexPaymentInput'

    def __init__(self, credit_card_number, expiry_date, cid, card_holder,
                 email_address):
        self.credit_card_number = credit_card_number
        self.expiry_date = expiry_date
        self.cid = cid
        self.card_holder = card_holder
        self.email_address = email_address

    def to_xml(self, factory):
        node = factory.create('ns0:amexPaymentInput')
        node.creditCardNumber = self.credit_card_number
        node.expiryDate = self.expiry_date
        node.cid = self.cid
        node.cardHolder = unicode(self.card_holder)
        node.emailAddress = self.email_address
        return node


class MasterCardPayment(Payment):
    """
    Mastercard payment
    """
    payment_method = DocdataClient.PAYMENT_METHOD_MASTERCARD
    request_parameter = 'masterCardPaymentInput'

    def __init__(self, credit_card_number, expiry_date, cvc2, card_holder,
                 email_address):
        self.credit_card_number = credit_card_number
        self.expiry_date = expiry_date
        self.cvc2 = cvc2
        self.card_holder = unicode(card_holder)
        self.email_address = email_address

    def to_xml(self, factory):
        node = factory.create('ns0:masterCardPaymentInput')
        node.creditCardNumber = self.credit_card_number
        node.expiryDate = self.expiry_date
        node.cvc2 = self.cvc2
        node.cardHolder = unicode(self.card_holder)
        node.emailAddress = self.email_address
        return node


class DirectDebitPayment(Payment):
    """
    Direct debit payment.
    """
    payment_method = DocdataClient.PAYMENT_METHOD_DIRECT_DEBIT
    request_parameter = 'directDebitPaymentInput'

    def __init__(self, holder_name, holder_city, holder_country_code, bic,
                 iban):
        self.holder_name = holder_name
        self.holder_city = holder_city
        self.holder_country_code = holder_country_code
        self.bic = bic
        self.iban = iban

    def to_xml(self, factory):
        country = factory.create('ns0:country')
        country._code = self.holder_country_code

        node = factory.create('ns0:directDebitPaymentInput')
        node.holderName = unicode(self.holder_name)
        node.holderCity = unicode(self.holder_city)
        node.holderCountry = country
        node.bic = self.bic
        node.iban = self.iban
        return node


class IdealPayment(DirectDebitPayment):
    """
    Direct debit payment in The Netherlands.
    The visitor is redirected to the bank website where the payment is made,
    and then redirected back to the gateway.
    """
    payment_method = 'IDEAL'


class BankTransferPayment(Payment):
    """
    Bank transfer.
    https://support.docdatapayments.com/index.php?_m=knowledgebase&_a=viewarticle&kbarticleid=141&nav=0,7
    """
    payment_method = DocdataClient.PAYMENT_METHOD_BANK_TRANSFER
    request_parameter = 'bankTransferPaymentInput'

    def __init__(self, email_address):
        self.email_address = email_address

    def to_xml(self, factory):
        node = factory.create('ns0:bankTransferPaymentInput')
        node.emailAddress = self.email_address
        return node


class ElvPayment(Payment):
    """
    The German Electronic Direct Debit (Elektronisches Lastschriftverfahren or ELV)
    """
    payment_method = DocdataClient.PAYMENT_METHOD_ELV
    request_parameter = 'elvPaymentInput'

    def __init__(self, account_number, bank_code):
        self.account_number = account_number
        self.bank_code = bank_code

    def to_xml(self, factory):
        node = factory.create('ns0:elvPaymentInput')
        node.accountNumber = self.account_number
        node.bankCode = self.bank_code
        return node
