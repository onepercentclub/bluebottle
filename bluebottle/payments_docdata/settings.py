# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL',),
        'supports_recurring': False,
    },

    {
        'provider': 'docdata',
        'id': 'direct-debit',
        'profile': 'directdebit',
        'name': 'Direct Debit',
        'max_amount': 10000,
        'restricted_countries': ('NL',),
        'supports_recurring': True,
        'supports_single': False,
    },

    {
        'provider': 'docdata',
        'id': 'creditcard',
        'profile': 'creditcard',
        'name': 'Credit Cards',
        'supports_recurring': False,
    },

    {
        'provider': 'docdata',
        'id': 'webmenu',
        'profile': 'webmenu',
        'name': 'Web Menu',
        'supports_recurring': True,
    }
)