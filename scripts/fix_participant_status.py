from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import DeadlineRegistration


def run(*args):
    for client in Client.objects.filter(schema_name='deloitte_uk').all():
        with LocalTenant(client):
            for reg in DeadlineRegistration.objects.filter(activity__status='succeeded').filter(status='new').all():
                reg.states.accept(save=True)
