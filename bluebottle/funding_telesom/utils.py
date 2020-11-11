from django.db import connection

from bluebottle.funding_telesom.tasks import start_payment


def initiate_payment(payment):
    payment.amount = payment.donation.amount.amount
    payment.currency = 'USD'
    payment.save()
    start_payment.delay(payment, tenant=connection.tenant)
    return payment


def update_payment(payment, data):
    if data['state'] == 'approved':
        payment.states.succeed(save=True)
    else:
        payment.states.fail(save=True)
    payment.save()
    return payment
