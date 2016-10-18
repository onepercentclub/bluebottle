# Either import these settings in your base.py or write your own.

MOCK_PAYMENT_METHODS = (
    {
        'provider': 'mock',
        'id': 'mock-paypal',
        'profile': 'paypal',
        'name': 'MockPal',
        'supports_recurring': False,
        'currencies': ['EUR'],
    },
    {
        'provider': 'mock',
        'id': 'mock-ideal',
        'profile': 'ideal',
        'name': 'MockDeal',
        'restricted_countries': ('NL',),
        'supports_recurring': False,
        'currencies': ['USD', 'EUR'],
    },
    {
        'provider': 'mock',
        'id': 'mock-creditcard',
        'profile': 'creditcard',
        'name': 'MockCard',
        'supports_recurring': False,
        'currencies': ['USD'],
    }
)

MOCK_FEES = {
    'creditcard': '3.5%',
    'ideal': 0.75,
    'paypal': '3%'
}
