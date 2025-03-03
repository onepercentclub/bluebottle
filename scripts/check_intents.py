from datetime import timedelta

from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.funding_stripe.models import PaymentIntent, StripePayment


def run(*args):
    fix = 'fix' in args
    start = now() - timedelta(days=100)
    for client in Client.objects.filter(schema_name='voor_apeldoorn').all():
        with (LocalTenant(client)):
            print('##### Client:', client.name)
            intents = PaymentIntent.objects.filter(created__gt=start).all()
            count = intents.count()
            print(f'Checking {count} intents')
            for intent in intents:
                payment = StripePayment.objects.filter(payment_intent=intent).first()
                if not payment:
                    if intent.intent.status == 'requires_payment_method':
                        continue
                    print(
                        f'{client.name} ;{intent.donation.id} ;'
                        f'No payment id for intent remote: {intent.intent.status}')
                    if fix:
                        payment = intent.get_payment()
                        payment.update()
                        print(f'{client.name} ;{intent.donation.id} ;New status {intent.donation.status}')
                else:
                    if intent.intent.status == 'requires_payment_method':
                        continue
                    if intent.intent.status == intent.donation.status:
                        continue
                    charge = intent.intent.charges and len(intent.intent.charges) and intent.intent.charges.data[0]
                    if intent.donation.status == 'activity_refunded' and intent.intent.status == 'succeeded':
                        if charge.refunded:
                            continue
                        print(
                            f'{client.name} ;{intent.donation.id} ; '
                            f'Should have been refunded, but remote {intent.intent.status}')
                    else:
                        print(
                            f'{client.name} ;{intent.donation.id} ;'
                            f'Local: {intent.donation.status} vs remote: {intent.intent.status}')
                        if fix:
                            payment = intent.get_payment()
                            payment.update()
                            print(f'{client.name} ;{intent.donation.id} ;New status {intent.donation.status}')

            print('Done!')
    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually fix the statuses.")
