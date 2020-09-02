import re

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding_stripe.utils import stripe
from bluebottle.funding_stripe.models import StripePayoutAccount


def run(*args):
    for client in Client.objects.all():
        print((client.schema_name))
        with LocalTenant(client):
            for account in StripePayoutAccount.objects.filter(
                account_id__isnull=False
            ):
                try:
                    if len(account.owner.activities.all()):
                        url = account.owner.activities.first().get_absolute_url()
                    else:
                        url = 'https://{}'.format(client.domain_url)

                    if 'localhost' in url:
                        url = re.sub('localhost', 't.goodup.com', url)

                    stripe.Account.modify(
                        account.account_id,
                        business_profile={
                            'url': url,
                            'mcc': '8398'
                        },
                    )
                    print(url)
                except Exception as e:
                    print(e)
