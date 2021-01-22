"""
behave environment module for testing behave-django
"""
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.test.utils import JSONAPITestClient


def before_all(context):
    connection.set_schema_to_public()
    tenant, _c = Client.objects.get_or_create(
        domain_url='behave',
        name='Behave',
        schema_name='behave',
        client_name='behave')
    connection.set_tenant(tenant)
    context.client = JSONAPITestClient()
