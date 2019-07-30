import requests
from django.core.exceptions import ImproperlyConfigured

from bluebottle.funding.exception import PaymentException


def post(url, data):
    response = requests.post(url, json=data)
    if response.status_code != 200:
        raise PaymentException(response.content)
    return response.json()


def check_payment_status(payment):

    verify_url = "https://api.ravepay.co/flwv3-pug/getpaidx/api/v2/verify"

    from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider
    provider = FlutterwavePaymentProvider.objects.first()

    if not provider:
        raise PaymentException('Flutterwave not enabled')

    data = {
        'txref': payment.tx_ref,
        'SECKEY': provider.private_settings['sec_key']
    }
    data = post(verify_url, data)
    payment.update_response = data
    if data['data']['status'] == 'successful':
        payment.transitions.succeed()
    else:
        payment.transitions.fail()
    payment.save()
    return payment


def get_flutterwave_settings():
    from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider
    provider = FlutterwavePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Flutterwave not enabled for this tenant')
    return provider.public_settings
