# Either import these settings in your base.py or write your own.

DOCDATA_PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL', 'Netherlands'),
        'supports_recurring': False,
    },
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'supports_recurring': False,
    },
    {
        'provider': 'docdata',
        'id': 'docdata-paypal',
        'profile': 'paypal',
        'name': 'Paypal',
        'supports_recurring': False,
    },
    {
        'provider': 'docdata',
        'id': 'docdata-directdebit',
        'profile': 'directdebit',
        'name': 'Direct Debit',
        'supports_recurring': True,
    }
)

DOCDATA_SETTINGS = {
    'profile': 'webmenu',
    'days_to_pay': 5,
    'testing_mode': True,
}
