# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = (
    {
        'provider': 'mock',
        'id': 'mock-paypal',
        'profile': 'paypal',
        'name': 'PayPal',
        'supports_recurring': False,
    },
    {
        'provider': 'mock',
        'id': 'mock-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL',),
        'supports_recurring': False,
    },
    {
        'provider': 'mock',
        'id': 'mock-creditcard',
        'profile': 'creditcard',
        'name': 'Credit Card',
        'supports_recurring': False,
    }
)