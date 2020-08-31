import datetime

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from django.utils.timezone import get_current_timezone

from bluebottle.funding.models import Funding


def run(*args):
    for client in Client.objects.all():
        with LocalTenant(client):
            for funding in Funding.objects.all():
                if funding.deadline and funding.duration:
                    old_deadline = funding.deadline
                    new_deadline = get_current_timezone().localize(
                        datetime.datetime(
                            old_deadline.year,
                            old_deadline.month,
                            old_deadline.day,
                            hour=23,
                            minute=59,
                            second=59
                        )
                    )
                    funding.deadline = new_deadline
                    funding.save()
                    funding.refresh_from_db()
                    print client.client_name,
                    print funding.id,
                    print old_deadline,
                    print '=>',
                    print new_deadline
                    print '=>',
                    print funding.deadline
