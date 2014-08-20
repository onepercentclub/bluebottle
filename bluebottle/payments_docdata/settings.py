# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL',),
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
        'supports_recurring': True,
    }
)