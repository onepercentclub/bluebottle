# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = (
    {
        'provider': 'mollie',
        'id': 'mollie-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL',),
        'supports_recurring': False,
    },
    {
        'provider': 'mollie',
        'id': 'mollie-creditcard',
        'profile': 'creditcard',
        'name': 'Credit Card',
        'supports_recurring': False,
    }
)