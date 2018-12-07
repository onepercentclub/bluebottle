from django.core.exceptions import ImproperlyConfigured
from bluebottle.clients import properties


def get_webhook_secret():
    for account in properties.MERCHANT_ACCOUNTS:
        if account['merchant'] == 'stripe':
            return account['webhook_secret']

    raise ImproperlyConfigured('No merchant account for stripe')
