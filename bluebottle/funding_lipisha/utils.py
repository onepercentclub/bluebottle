import json

from lipisha import Lipisha, lipisha
from moneyed import Money

from bluebottle.clients import properties
from bluebottle.fsm import TransitionNotPossible
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import Donation
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaPayment, LipishaBankAccount


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
    This will initiate a payment at Lipisha.
    It will send a push notification to the user's phone.
    They just have to confirm with there pin to authorise the payment.
    """
    client = init_client()
    account_number = payment.donation.activity.bank_account.mpesa_code

    response = client.request_money(
        account_number=account_number,
        mobile_number=payment.mobile_number,
        method=payment.method,
        amount=int(payment.donation.amount.amount),
        currency=payment.donation.amount.currency,
        reference=payment.unique_id
    )

    if response['status']['status'] == 'SUCCESS':
        payment.transaction = response['content']['transaction']
        payment.save()
    else:
        payment.states.fail(save=True)
        raise PaymentException(response['status']['status_description'])
    return payment


def check_payment_status(payment):
    client = init_client()

    # If we have a transaction reference, then use that
    if payment.transaction:
        response = client.get_transactions(
            transaction_type='Payment',
            transaction=payment.transaction
        )
    else:
        response = client.get_transactions(
            transaction_type='Payment',
            transaction_merchant_reference=payment.unique_id
        )

    payment.update_response = json.dumps(response)
    data = response['content']
    if len(data) == 0:
        try:
            payment.states.fail()
        except TransitionNotPossible:
            pass
        payment.save()
        raise PaymentException('Payment could not be verified yet. Payment not found.')
    else:
        data = data[0]
        if data['transaction_amount'] != payment.donation.amount.amount:
            # Update donation amount based on the amount registered at Lipisha
            amount = Money(data['transaction_amount'], 'KES')
            payment.donation.amount = amount
        payment.donation.name = data['transaction_name'].replace('+', ' ').title()
        payment.donation.save()

    payment.mobile_number = data['transaction_mobile_number']

    if data['transaction_status'] in ['Completed', 'Settled', 'Acknowledged', 'Authorized']:
        try:
            payment.states.succeed()
        except TransitionNotPossible:
            pass
    if data['transaction_status'] in ['Cancelled', 'Voided']:
        try:
            payment.states.fail()
        except TransitionNotPossible:
            pass
    if data['transaction_reversal_status'] == 'Reverse' or data['transaction_status'] in ['Reversed']:
        try:
            payment.states.refund()
        except TransitionNotPossible:
            pass
    payment.save()


def generate_success_response(payment):
    donation = payment.donation
    message = "Dear {}, thanks for your donation {} of {} {} to {}!".format(
        donation.name,
        payment.transaction,
        donation.amount.currency,
        donation.amount.amount,
        donation.activity.title
    )
    credentials = get_credentials()

    return {
        "api_key": credentials['api_key'],
        # "api_signature": credentials['api_signature'],
        "api_version": "1.0.4",
        "api_type": "Receipt",
        "transaction_reference": payment.transaction,
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


def initiate_payment(data):
    """
    Look for an existing payment and update that or create a new one.
    """
    account_number = data['transaction_account_number']
    transaction_merchant_reference = data['transaction_merchant_reference']
    transaction_reference = data['transaction_reference']
    payment = None
    credentials = get_credentials()

    # Credentials should match
    if credentials['api_key'] != data['api_key']:
        return generate_error_response(transaction_reference)
    if credentials['api_signature'] != data['api_signature']:
        return generate_error_response(transaction_reference)

    # If account number has a # then it is a donation started at our platform
    if transaction_merchant_reference:
        try:
            payment = LipishaPayment.objects.get(unique_id=transaction_merchant_reference)
        except LipishaPayment.DoesNotExist:
            # Payment not found
            pass

    if transaction_reference:
        try:
            payment = LipishaPayment.objects.get(transaction=transaction_reference)
        except LipishaPayment.DoesNotExist:
            # Payment not found
            pass

    if not payment:
        # If we haven't found a payment by now we should create a new donation
        try:
            account = LipishaBankAccount.objects.get(mpesa_code=account_number)
            funding = account.funding
        except LipishaBankAccount.DoesNotExist:
            return generate_error_response(transaction_reference)

        name = data['transaction_name'].replace('+', ' ').title()

        donation = Donation.objects.create(
            amount=Money(data['transaction_amount'], data['transaction_currency']),
            name=name,
            activity=funding)

        payment = LipishaPayment.objects.create(
            donation=donation,
            transaction=transaction_reference,
        )
    try:
        check_payment_status(payment)
    except PaymentException:
        pass
    payment.save()
    return generate_success_response(payment)


def acknowledge_payment(data):
    """
    Find existing payment and switch to given status
    """
    transaction_reference = data['transaction_reference']
    credentials = get_credentials()

    # Credentials should match
    if credentials['api_key'] != data['api_key']:
        return generate_error_response(transaction_reference)
    if credentials['api_signature'] != data['api_signature']:
        return generate_error_response(transaction_reference)

    try:
        payment = LipishaPayment.objects.get(transaction=transaction_reference)
    except LipishaPayment.DoesNotExist:
        return generate_error_response(transaction_reference)
    except LipishaPayment.MultipleObjectsReturned:
        payment = LipishaPayment.objects.filter(transaction=transaction_reference).last()

    # payment.mobile_number = data['transaction_mobile_number']

    try:
        check_payment_status(payment)
    except PaymentException:
        pass
    payment.save()
    return generate_success_response(payment)
