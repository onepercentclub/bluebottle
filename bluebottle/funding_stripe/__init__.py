from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE['api_key']
stripe.webhook_secret = settings.STRIPE['webhook_secret']
