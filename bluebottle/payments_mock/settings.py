# Either import these settings in your base.py or write your own.

MOCK_PAYMENT_METHODS = (
    {
        'provider': 'mock',
        'id': 'mock-paypal',
        'profile': 'paypal',
        'name': 'MockPal',
        'currencies': {
            'EUR': {'min_amount': 5, 'max_amount': 100}
        }
    },
    {
        'provider': 'mock',
        'id': 'mock-ideal',
        'profile': 'ideal',
        'name': 'MockDeal',
        'restricted_countries': ('NL',),
        'currencies': {
            'EUR': {'min_amount': 5},
            'USD': {'min_amount': 5},
        }
    },
    {
        'provider': 'mock',
        'id': 'mock-creditcard',
        'profile': 'creditcard',
        'name': 'MockCard',
        'currencies': {
            'USD': {'min_amount': 5},
        }
    }
)

MOCK_FEES = {
    'creditcard': '3.5%',
    'ideal': 0.75,
    'paypal': '3%'
}
