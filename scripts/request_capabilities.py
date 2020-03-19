from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding_stripe.utils import stripe
from bluebottle.funding_stripe.models import StripePayoutAccount


def run(*args):
    for client in Client.objects.all():
        with LocalTenant(client):
            for account in StripePayoutAccount.objects.filter(
                account_id__isnull=False
            ):
                try:
                    stripe.Account.modify(
                        account.account_id,
                        requested_capabilities=["legacy_payments", "transfers"],
                    )
                    print account.account.capabilities
                except Exception, e:
                    print e
