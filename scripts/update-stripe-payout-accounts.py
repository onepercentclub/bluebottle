from parler.utils.conf import ImproperlyConfigured

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.funding_stripe.utils import get_stripe


def run(*args):
    for tenant in Client.objects.all():
        with LocalTenant(tenant):
            accounts = StripePayoutAccount.objects.all().order_by('-created')

            print(tenant.client_name, len(accounts))

            try:
                for account in accounts:
                    stripe = get_stripe()
                    stripe_account = stripe.Account.retrieve(account.account_id)

                    account.requirements = stripe_account.requirements.eventually_due

                    try:
                        account.verified = stripe_account.individual.verification.status == "verified"
                    except AttributeError:
                        pass

                    account.payments_enabled = stripe_account.charges_enabled
                    account.payouts_enabled = stripe_account.payouts_enabled

                    if account.status == 'verified' and (
                        not account.verified or
                        account.requirements != [] or
                        not stripe_account.charges_enabled or
                        not stripe_account.payouts_enabled
                    ):
                        account.states.set_incomplete()

                    account.execute_triggers(send_messages=False)

                    account.save()
            except ImproperlyConfigured:
                pass
