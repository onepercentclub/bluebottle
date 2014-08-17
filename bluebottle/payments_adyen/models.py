from bluebottle.payments.models import Payment
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django.utils.translation import ugettext as _
from django.db import models
from django_countries.fields import CountryField


class AdyenPayment(Payment):

    """
    - merchantAccount
    The merchant account for which you want to process the payment.
    - amount
    A container for the data concerning the amount to be authorised. This should contain the following items:
    - currency
    The three character ISO currency code.
    - value
    The paymentAmount of the transaction.
    Please note, the transaction amount should be provided in minor units according to ISO standards;
    some currencies don't have decimal points, such as JPY, and some have 3 decimal points, such as BHD.
    For example, 10 GBP would be submitted with a value of "1000" and 10 JPY would be submitted as
    "10".
    - reference
    This is your reference for this payment, it will be used in all communication to you regarding the status of the
    payment. We recommend using a unique value per payment but this is not a requirement. If you need to provide
    multiple references for a transaction you may use this field to submit them with the transaction, separating each
    with "-".
    This field has a maximum of 80 characters.
    - shopperIP (recommended)
    The IP address of the shopper. We recommend that you provide this data, as it is used in a number of risk
    checks, for example, number of payment attempts, location based checks.
    - shopperEmail (recommended)
    The shopper's email address. We recommend that you provide this data, as it is used in a velocity fraud check.
    Please note, this feld is required for Recurring payments.
    - shopperReference (recommended)
    An ID that uniquely identifies the shopper, such as a customer id in a shopping cart system. We recommend that
    you provide this data, as it is used in a velocity fraud check and is the key for recurring payments.
    Please note, this field is required for Recurring payments.
    - fraudOfset (optional)
    An integer that is added to the normal fraud score. The value can be either positive or negative.
    - selectedBrand (optional)
    Used with some payment methods to indicate how it should be processed. For the MisterCash payment method
    it can be set to maestro (default) to be processed like a Maestro card or bcmc to be processed as a MisterCash
    card.
    """
    customer_id = models.PositiveIntegerField(default=0)  # Defaults to 0 for anonymous.
    email = models.EmailField(max_length=254, default='')
    first_name = models.CharField(max_length=200, default='')
    last_name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, default='')
    postal_code = models.CharField(max_length=20, default='')
    city = models.CharField(max_length=200, default='')
    country = CountryField()
    language = models.CharField(max_length=2, default='en')

