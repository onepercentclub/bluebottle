import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_stripe_settings():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        return
    return provider.public_settings


def get_stripe():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')

    stripe.api_key = provider.stripe_secret or settings.STRIPE['api_key']
    stripe.api_version = '2024-11-20.acacia'
    stripe.webhook_secret_checkout = provider.webhook_secret_checkout or settings.STRIPE['webhook_secret_checkout']
    stripe.webhook_secret_intents = provider.webhook_secret_intents or settings.STRIPE['webhook_secret_intents']
    stripe.webhook_secret_connect = provider.webhook_secret_connect or settings.STRIPE['webhook_secret_connect']
    return stripe
