
from calendar import different_locale
from django.db.models import Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.funding_stripe.models import StripePayoutAccount

def run(*args):
    for tenant in Client.objects.all():
        with LocalTenant(tenant):
            accounts = StripePayoutAccount.objects.all().order_by('-created')

            print(tenant.client_name, len(accounts))

            for account in accounts:
                stripe = get_stripe()
                stripe_account = stripe.Account.retrieve(account.account_id)

                if stripe_account.individual:
                    account.requirements = stripe_account.individual.requirements.eventually_due

                    try:
                        account.verified = stripe_account.individual.verification.status == "verified"
                    except AttributeError:
                        pass

                account.payments_enabled = stripe_account.charges_enabled
                account.payouts_enabled = stripe_account.payouts_enabled

                account.execute_triggers(send_messages=False)
                account.save()
                print(
                    account.pk,
                    account.account_id,
                    account.status,
                    account.verified,
                    account.required_fields,
                    account.payments_enabled,
                    account.payouts_enabled
                )
