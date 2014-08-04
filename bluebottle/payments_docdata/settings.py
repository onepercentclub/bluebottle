# Either import these settings in your base.py or write your own.

PAYMENT_METHODS = {
    'provider_name': 'docdata',
    'provider_prefix': 'dd',
    'app_name': 'payments_docadata',
    'methods': {
        'ideal': {
            'id': 'IDEAL',
            'profile': 'ideal',
            'name': 'iDeal',
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

        'direct-debit': {
            'id': 'SEPA_DIRECT_DEBIT',
            'profile': 'directdebit',
            'name': 'Direct Debit',
            'max_amount': 10000,
            'restricted_countries': ('NL',),
            'supports_recurring': True,
            'supports_single': False,
        },

        'creditcard': {
            'profile': 'creditcard',
            'name': 'Credit Cards',
            'supports_recurring': False,
        },

        'webmenu': {
            'profile': 'webmenu',
            'name': 'Web Menu',
            'supports_recurring': True,
        }
    }
}