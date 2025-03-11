from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.models import ActivitySearchFilter


def run(*args):
    for tenant in Client.objects.all().all():
        with LocalTenant(tenant):
            print(f'Fixing {tenant.name}')
            ActivitySearchFilter.objects.filter(
                type__in=['managing', 'status']
            ).all().delete()
