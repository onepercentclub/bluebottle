# Either import these settings in your base.py or write your own.

_ = lambda s: s

DOCDATA_PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': _('iDEAL'),
        'restricted_countries': ('NL', 'Netherlands'),
    },
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': _('CreditCard'),
    },
    {
        'provider': 'docdata',
        'id': 'docdata-paypal',
        'profile': 'paypal',
        'name': _('Paypal'),
    },
    {
        'provider': 'docdata',
        'id': 'docdata-directdebit',
        'profile': 'directdebit',
        'name': _('Direct Debit'),
    }
)

DOCDATA_SETTINGS = {
    'profile': 'webmenu',
    'days_to_pay': 5,
    'testing_mode': True,
}
