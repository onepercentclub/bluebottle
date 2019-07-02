from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE['api_key']
stripe.webhook_secret = settings.STRIPE['webhook_secret']
stripe.webhook_secret_connect = settings.STRIPE['webhook_secret_connect']
stripe.api_version = '2019-05-16'
