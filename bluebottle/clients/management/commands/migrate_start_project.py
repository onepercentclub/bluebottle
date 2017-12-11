from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.pages.models import Page

from fluent_contents.models import Placeholder
from fluent_contents.plugins.rawhtml.models import RawHtmlItem


class Command(BaseCommand):
    help = 'Create homepage from settings'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to import the homepage for")
        parser.add_argument('--all', '-a', action='store_true', dest='all',
                            default=False, help="Import all tenants")

    def handle(self, *args, **options):
        if options['all']:
            tenants = Client.objects.all()

        if options['tenant']:
            tenants = [Client.objects.get(schema_name=options['tenant'])]

        for client in tenants:
            print "\n\nCreating start project page for {}".format(client.name)
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                Page.objects.filter(slug='start-project').delete()
                try:
                    for language, content in properties.START_PROJECT.items():
                        page = Page(
                            title=content['title'],
                            slug='start-project',
                            full_page=True,
                            language=language,
                            publication_date=now(),
                            status='published',
                        )
                        page.save()

                        page_type = ContentType.objects.get_for_model(page)

                        (placeholder, _created) = Placeholder.objects.get_or_create(
                            parent_id=page.pk,
                            parent_type_id=page_type.pk,
                            title='Body',
                            slot='blog_contents',
                        )
                        block_type = ContentType.objects.get_for_model(RawHtmlItem)

                        RawHtmlItem.objects.create_for_placeholder(
                            placeholder,
                            polymorphic_ctype=block_type,  # This does not get set automatically in migrations
                            html=content['content']
                        )
                except AttributeError:
                    pass
