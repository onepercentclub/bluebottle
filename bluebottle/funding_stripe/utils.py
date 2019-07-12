from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import stripe


def get_stripe_settings():
    from bluebottle.funding_stripe.models import StripePaymentProvider
    provider = StripePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Stripe not enabled for this tenant')
    return provider.public_settings


stripe.api_key = settings.STRIPE['api_key']
stripe.webhook_secret = settings.STRIPE['webhook_secret']
stripe.webhook_secret_connect = settings.STRIPE['webhook_secret_connect']
