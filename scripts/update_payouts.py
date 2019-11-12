import json

from django.db import transaction

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.funding.models import Payout, Donation


def run(*args):
    with open(args[0]) as json_file:
        payouts = json.load(json_file)

    mapping = []

    for client in Client.objects.all():
        with LocalTenant(client):
            Payout.objects.exclude(status='new').delete()

            tenant_payouts = [payout for payout in payouts if payout['tenant'] == client.client_name]

            models = []
            for payout in tenant_payouts:
                model = Payout(
                    activity_id=payout['activity_id'],
                    status=payout['status'],
                    created=payout['created'],
                    updated=payout['updated'],
                    provider=payout['method'],
                    currency=payout['currency'],
                )
                models.append((payout, model))

            Payout.objects.bulk_create(model[1] for model in models)

            with transaction.atomic():
                for payout, model in models:
                    for donation in Donation.objects.filter(
                        pk__in=payout['donations']
                    ):
                        donation.payout_id = model.pk
                        donation.save()

            mapping += [(payout['id'], model.pk) for (payout, model) in models]

    print json.dumps(mapping)
