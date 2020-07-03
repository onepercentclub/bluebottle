import requests
from django.utils.timezone import now

from bluebottle.funding_telesom.models import TelesomPaymentProvider


def get_credentials():
    provider = TelesomPaymentProvider.objects.get()
    return provider.private_settings


def initiate_payment(payment):
    credentials = get_credentials()
    data = {
        "schemaVersion": "1.0",
        "requestId": payment.unique_id,
        "timestamp": now().strftime("%Y-%m-%d, %H:%M:%S"),
        "channelName": "WEB",
        "serviceName": "API_PURCHASE",
        "sessionId": "sdfsdfs",

        "serviceParams": {
            "merchantUid": "M0910002",
            "apiUserId": "1000010",
            "apiKey": "APIXTOIWEHSDLKOSEKYR",
            "paymentMethod": "MWALLET_ACCOUNT",

            "payerInfo": {
                "accountNo": payment.account_number,
                "accountHolder": payment.account_name
            },

            "transactionInfo": {
                "referenceId": "56werw278",
                "invoiceId": "123werwer4",
                "amount": "50",
                "currency": "USD",
                "description": "donation 1234"
            }
        }
    }
    response = requests.post(credentials.api_url, json=data)
    return response
