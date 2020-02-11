import requests
from django.core.exceptions import ImproperlyConfigured

from bluebottle.funding.exception import PaymentException
from bluebottle.funding.transitions import PaymentTransitions


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
    try:
        data = post(verify_url, data)
    except PaymentException:
        if payment.status != PaymentTransitions.values.failed:
            payment.transitions.fail()
        payment.save()
        return payment

    payment.update_response = data
    if payment.donation.amount != data['data']['amount']:
        payment.donation.amount = data['data']['amount']
        payment.donation.save()
    if data['data']['status'] == 'successful':
        if payment.status != PaymentTransitions.values.succeeded:
            payment.transitions.succeed()
    else:
        if payment.status != PaymentTransitions.values.failed:
            payment.transitions.fail()
    payment.save()
    return payment


def get_flutterwave_settings():
    from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider
    provider = FlutterwavePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Flutterwave not enabled for this tenant')
    return provider.public_settings
