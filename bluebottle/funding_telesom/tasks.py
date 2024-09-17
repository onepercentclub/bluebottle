import requests
from celery import shared_task
from django.utils.timezone import now

from bluebottle.clients.utils import LocalTenant
from bluebottle.funding_telesom.models import TelesomPaymentProvider


def get_credentials():
    provider = TelesomPaymentProvider.objects.get()
    return provider.private_settings


@shared_task
def start_payment(payment, tenant):
    with LocalTenant(tenant, clear_tenant=True):
        credentials = get_credentials()
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
        payment.response = data
        if data['params'] and data['params']['state'] == 'APPROVED':
            payment.states.succeed(save=True)
        else:
            payment.states.fail(save=True)
        payment.save()
