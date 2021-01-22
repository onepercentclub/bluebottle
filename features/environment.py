"""
behave environment module for testing behave-django
"""
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.members.models import Member
from bluebottle.test.utils import JSONAPITestClient


def before_all(context):
    pass


def django_ready(context, scenario=None):
    connection.set_schema_to_public()
    context.tenant, _c = Client.objects.get_or_create(
        domain_url='behave',
        name='Behave',
        schema_name='behave',
        client_name='behave')
    connection.set_tenant(context.tenant)
    context.test.client = JSONAPITestClient()
    Member.objects.all().delete()
