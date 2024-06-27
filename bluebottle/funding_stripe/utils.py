import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_stripe_settings():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')
    return provider.public_settings


def get_stripe():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')
    api_key = provider.stripe_secret or settings.STRIPE['api_key'],
    stripe.api_key = api_key
    stripe.api_version = '2019-09-09'
    stripe.webhook_secret_sources = api_key
    stripe.webhook_secret_intents = api_key
    stripe.webhook_secret_connect = api_key
    return stripe
