import json

from lipisha import Lipisha, lipisha
from moneyed import Money

from bluebottle.clients import properties
from bluebottle.funding.exception import PaymentException
from bluebottle.funding_lipisha.models import LipishaPaymentProvider


def check_payment_status(payment):
    provider = LipishaPaymentProvider.objects.get()

    live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
    if live_mode:
        env = lipisha.PRODUCTION_ENV
    else:
        env = lipisha.SANDBOX_ENV
    client = Lipisha(
        provider.private_settings['api_key'],
        provider.private_settings['api_signature'],
        api_environment=env
    )

    # If we have a transaction reference, then use that
    response = client.get_transactions(
        transaction_type='Payment',
        transaction_reference=payment.reference_id
    )

    payment.update_response = json.dumps(response)
    data = response['content']

    if len(data) == 0:
        payment.transitions.fail()
        payment.save()
        raise PaymentException('Payment could not be verified yet. Payment not found.')
    else:
        payment = data[0]
        if payment.transaction_amount != payment.donation.amount.amount:
            # Update donation amount based on the amount registered at Lipisha
            amount = Money(payment.transaction_amount, 'KES')
            payment.donation.amount = amount
            payment.donation.save()

    """
    FIXME
    Trigger the right transitions now
    STATUS_MAPPING = {
        'Requested': StatusDefinition.CREATED,
        'Completed': StatusDefinition.SETTLED,
        'Cancelled': StatusDefinition.CANCELLED,
        'Voided': StatusDefinition.FAILED,
        'Acknowledged': StatusDefinition.AUTHORIZED,
        'Authorized': StatusDefinition.AUTHORIZED,
        'Settled': StatusDefinition.SETTLED,
        'Reversed': StatusDefinition.REFUNDED
    }
    """
    payment.save()
