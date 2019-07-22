import json

from lipisha import Lipisha, lipisha
from moneyed import Money

from bluebottle.clients import properties
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import Donation, Funding
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaPayment


def get_credentials():
    provider = LipishaPaymentProvider.objects.get()
    return provider.private_settings


def init_client():
    live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
    if live_mode:
        env = lipisha.PRODUCTION_ENV
    else:
        env = lipisha.SANDBOX_ENV
    credentials = get_credentials()
    return Lipisha(
        credentials['api_key'],
        credentials['api_signature'],
        api_environment=env
    )


def initiate_push_payment(payment):
    """
    This will iniate a payment at Lipisha. It will send a push notification to the user's phone.
    They just have to confirm with there pin to authorise the payment.
    """
    client = init_client()
    provider = LipishaPaymentProvider.objects.get()

    response = client.request_money(
        account_number=provider.paybill,
        mobile_number=payment.mobile_number,
        method=payment.method,
        amount=int(payment.donation.amount.amount),
        currency=payment.donation.amount.currency,
        reference=payment.unique_id
    )
    """
    {
        u'status': {
            u'status': u'SUCCESS',
            u'status_code': u'0000',
            u'status_description': u'Payment Requested'
        },
        u'content': {
            u'transaction': u'UUZUEHSSX',
            u'reference': u'local-40',
            u'amount': u'789',
            u'account_number': u'08857',
            u'mobile_number': u'254',
            u'method': u'Paybill (M-Pesa)'
        }
    }

    {
        u'status': {
            u'status': u'FAIL',
            u'status_code': 3000,
            u'status_description': u'Invalid API Credentials'
        },
        u'content': []
    }
    """
    if response['status']['status'] == 'SUCCESS':
        payment.transaction = response['content']['transaction']
        payment.save()
    else:
        payment.transitions.fail()
        payment.save()
        raise PaymentException(response['status']['status_description'])
    return payment


def check_payment_status(payment):
    client = init_client()

    # If we have a transaction reference, then use that
    response = client.get_transactions(
        transaction_type='Payment',
        transaction_reference=payment.unique_id
    )

    payment.update_response = json.dumps(response)
    data = response['content']

    if len(data) == 0:
        payment.transitions.fail()
        payment.save()
        raise PaymentException('Payment could not be verified yet. Payment not found.')
    else:
        data = data[0]
        if data.transaction_amount != payment.donation.amount.amount:
            # Update donation amount based on the amount registered at Lipisha
            amount = Money(data.transaction_amount, 'KES')
            payment.donation.amount = amount
            payment.donation.save()

    if data.transaction_status in ['Completed', 'Settled', 'Acknowledged', 'Authorized']:
        payment.transitions.succeed()
    if data.transaction_status in ['Cancelled', 'Voided']:
        payment.transactions.fail()
    if data.transaction_status in ['Reversed']:
        payment.transactions.refund()

    payment.save()


def generate_success_response(payment):
    donation = payment.order_payment.order.donations.first()
    message = "Dear {}, thanks for your donation {} of {} {} to {}!".format(
        donation.name,
        payment.transaction_reference,
        payment.transaction_currency,
        payment.transaction_amount,
        donation.project.title
    )
    credentials = get_credentials()

    return {
        "api_key": credentials['api_key'],
        # "api_signature": credentials['api_signature'],
        "api_version": "1.0.4",
        "api_type": "Receipt",
        "transaction_reference": payment.transaction_reference,
        "transaction_status_code": "001",
        "transaction_status": "SUCCESS",
        "transaction_status_description": "Transaction received successfully.",
        "transaction_status_action": "ACCEPT",
        "transaction_status_reason": "VALID_TRANSACTION",
        "transaction_custom_sms": message
    }


def generate_error_response(reference):
    credentials = get_credentials()
    return {
        "api_key": credentials['api_key'],
        # "api_signature": credentials['api_signature'],
        "api_version": "1.0.4",
        "api_type": "Receipt",
        "transaction_reference": reference,
        "transaction_status_code": "002",
        "transaction_status": "FAIL",
        "transaction_status_description": "Transaction has a problem and we reject.",
        "transaction_status_action": "REJECT",
        "transaction_status_reason": "INVALID_TRANSACTION"
    }


def update_webhook_payment(data):
    # account_number = data['transaction_account_number']
    transaction_merchant_reference = data['transaction_merchant_reference']
    transaction_reference = data['transaction_reference']
    credentials = get_credentials()

    if credentials['api_key'] != data['api_key']:
        return generate_error_response(transaction_reference)
    if credentials['api_signature'] != data['api_signature']:
        return generate_error_response(transaction_reference)

    payment = None

    # Try to find a matching payment
    if transaction_merchant_reference:
        payment, created = LipishaPayment.objects.get_or_create(
            unique_id=transaction_merchant_reference
        )
    if transaction_reference:
        payment, created = LipishaPayment.objects.get_or_create(
            unique_id=transaction_merchant_reference
        )

    # Try to find an payout account with matching account_number
    if not payment:
        name = data['transaction_name'].replace('+', ' ').title()

        # FIXME: get the right Funding Activity
        funding = Funding.objects.first()

        donation = Donation.objects.create(
            amount=Money(data['transaction_amount'], data['transaction_currency']),
            name=name,
            activity=funding
        )
        payment = LipishaPayment.objects.create(
            donation=donation
        )

    payment.mobile_number = data['transaction_mobile']
    payment.reference = data['transaction_mobile']

    if data['transaction_status'] == 'Completed':
        payment.succeed()
    else:
        payment.fail()
    payment.reference = payment.order_payment_id
    payment.save()
    return payment
