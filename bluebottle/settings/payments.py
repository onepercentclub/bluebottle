from bluebottle.payments_docdata.settings import DOCDATA_SETTINGS  # noqa

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL', 'Netherlands'),
        'supports_recurring': False,
        'currencies': {'EUR': {}}
    },
    {
        'provider': 'docdata',
        'id': 'docdata-directdebit',
        'profile': 'directdebit',
        'name': 'Direct Debit',
        'supports_recurring': True,
        'currencies': {'EUR': {}}
    },
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'supports_recurring': False,
        'currencies': {'EUR': {}}
    }
)
VAT_RATE = 0.21
