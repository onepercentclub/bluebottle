import stripe

from bluebottle.payments.exception import PaymentException


def init_stripe():
    from bluebottle.funding_stripe.models import StripePaymentProvider

    settings = StripePaymentProvider.objects.first()
    if not settings:
        raise PaymentException('Stripe is not enabled for this tenant.')
    stripe.api_key = settings.private_settings['api_key']
    stripe.webhook_secret = settings.private_settings['webhook_secret']
    return stripe
