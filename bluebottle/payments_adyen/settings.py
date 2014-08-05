# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = (
    {
        'provider': 'adyen',
        'profile': 'ideal',
        'name': 'iDEAL',
        'submethods': {
            '0081': 'Fortis',
            '0021': 'Rabobank',
            '0721': 'ING Bank',
            '0751': 'SNS Bank',
            '0031': 'ABN Amro Bank',
            '0761': 'ASN Bank',
            '0771': 'SNS Regio Bank',
            '0511': 'Triodos Bank',
            '0091': 'Friesland Bank',
            '0161': 'van Lanschot Bankiers'
        },
        'restricted_countries': ('NL',),
        'supports_recurring': False,
    },
    {
        'provider': 'adyen',
        'profile': 'paypal',
        'name': 'PayPal',
        'max_amount': 1000,
        'supports_single': False,
    },
    {
        'provider': 'adyen',
        'profile': 'mastercard',
        'name': 'MasterCard',
        'supports_recurring': False,
    }
)