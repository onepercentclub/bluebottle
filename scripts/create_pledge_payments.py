from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding.models import Donation
from bluebottle.donations.models import Donation as OldDonation
from bluebottle.funding_pledge.models import PledgePayment


def run(*args):
    for client in Client.objects.all():
        with LocalTenant(client):
            print 'Migrating {}\n\n'.format(client.name)
            for donation in Donation.objects.select_related('payment').filter(
                payment__isnull=True,
                status='succeeded'
            ):
                try:
                    old_donation = OldDonation.objects.get(
                        new_donation_id=donation.pk,
                        order__order_payments__payment_method='pledgeStandard'
                    )
                    if (
                        old_donation.order.order_payment and
                        old_donation.order.order_payment.payment_method == 'pledgeStandard'
                    ):
                        print old_donation
                        PledgePayment.objects.create(
                            donation=donation,
                            status='succeeded'
                        )

                except OldDonation.DoesNotExist:
                    pass
