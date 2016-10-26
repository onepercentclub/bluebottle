from bluebottle.payments_docdata.settings import DOCDATA_SETTINGS

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL', 'Netherlands'),
        'supports_recurring': False,
        'currencies': {}
    },
    {
        'provider': 'docdata',
        'id': 'docdata-directdebit',
        'profile': 'directdebit',
        'name': 'Direct Debit',
        'supports_recurring': True,
        'currencies': {}
    },
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'supports_recurring': False,
        'currencies': {}
    }
)
VAT_RATE = 0.21
