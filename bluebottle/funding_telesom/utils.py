from decimal import Decimal

import requests
from django.utils.timezone import now

from bluebottle.funding_telesom.models import TelesomPaymentProvider


def get_credentials():
    provider = TelesomPaymentProvider.objects.get()
    return provider.private_settings


def initiate_payment(payment):
    credentials = get_credentials()
    payment.amount = Decimal(payment.donation.amount.amount) / 100
    payment.currency = 'USD'
    payment.save()
    data = {
        "schemaVersion": "1.0",
        "requestId": payment.unique_id,
        "timestamp": now().strftime("%Y-%m-%d, %H:%M:%S"),
        "channelName": "WEB",
        "serviceName": "API_PURCHASE",
        "sessionId": payment.unique_id,
        "serviceParams": {
            "merchantUid": credentials['merchant_uid'],
            "apiUserId": credentials['api_user_id'],
            "apiKey": credentials['api_key'],
            "paymentMethod": "MWALLET_ACCOUNT",

            "payerInfo": {
                "accountNo": payment.account_number,
                "accountHolder": payment.account_name
            },

            "transactionInfo": {
                "referenceId": payment.unique_id,
                "invoiceId": payment.unique_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "description": "donation {}".format(payment.donation_id)
            }
        }
    }
    response = requests.post(credentials['api_url'], json=data)
    data = response.json()
    payment.response = response
    if data['params'] and data['params']['state'] == 'approved':
        payment.states.succeed(save=True)
    else:
        payment.states.fail(save=True)
    return payment


def update_payment(payment, data):
    if data['state'] == 'approved':
        payment.states.succeed(save=True)
    else:
        payment.states.fail(save=True)
    return payment
