import stripe
from django.core.exceptions import ImproperlyConfigured


def get_private_key(key='secret_key'):
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')
    try:
        return provider.private_settings[key]
    except KeyError:
        raise ImproperlyConfigured('Stripe property missing {}'.format(key))


def get_stripe_settings():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')
    return provider.public_settings


def init_stripe():
    stripe.api_key = get_private_key('secret_key')
    stripe.webhook_secret = get_private_key('webhook_secret')
    return stripe
