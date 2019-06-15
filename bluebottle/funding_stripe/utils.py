import stripe
from django.conf import settings


class StripeMixin(object):

    _stripe = stripe

    @property
    def stripe(self):
        self._stripe.api_key = self.api_key
        return self._stripe

    # TODO: Load these settings through StripeProvider model
    @property
    def webhook_secret(self):
        return settings.STRIPE['private']['webhook_secret']

    @property
    def api_key(self):
        return settings.STRIPE['private']['api_key']
