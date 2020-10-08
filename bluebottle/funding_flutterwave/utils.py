from __future__ import absolute_import
import requests
from django.core.exceptions import ImproperlyConfigured

from bluebottle.funding.exception import PaymentException


def post(url, data):
    response = requests.post(url, json=data)
    if response.status_code != 200:
        raise PaymentException(response.content)
    return response.json()


def check_payment_status(payment):
    from .states import FlutterwavePaymentStateMachine
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
        if payment.status != FlutterwavePaymentStateMachine.failed.value:
            payment.states.fail()
        payment.save()
        return payment

    payment.update_response = data
    try:
        amount = data['data']['amountsettledforthistransaction']
    except KeyError:
        amount = data['data']['amount']

    payment.donation.amount = amount
    payment.donation.payout_amount = amount
    payment.donation.save()

    if data['data']['status'] == 'successful':
        from .states import FlutterwavePaymentStateMachine
        if payment.status != FlutterwavePaymentStateMachine.succeeded.value:
            payment.states.succeed()
    else:
        if payment.status != FlutterwavePaymentStateMachine.failed.value:
            payment.states.fail()
    payment.save()
    return payment


def get_flutterwave_settings():
    from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider
    provider = FlutterwavePaymentProvider.objects.first()
    if not provider:
        raise ImproperlyConfigured('Flutterwave not enabled for this tenant')
    return provider.public_settings
