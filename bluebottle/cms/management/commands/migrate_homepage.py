from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.core.files import File

import requests

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from fluent_contents.models import Placeholder, ContentItem

from bluebottle.cms.models import (
    HomePage,
)


class Command(BaseCommand):
    help = 'Create homepage from settings'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to import the homepage for")
        parser.add_argument('--all', '-a', action='store_true', dest='all',
                            default=False, help="Import all tenants")

    def create_block(self, block_type, block, placeholder, language):
        model = apps.get_model('cms', block_type)
        content_type = ContentType.objects.get_for_model(model)

        block['kwargs'] = dict(
            (key, val) for key, val in block['kwargs'].items() if val
        )

        content_block = model.objects.create_for_placeholder(
            placeholder,
            polymorphic_ctype=content_type,  # This does not get set automatically in migrations
            language_code=language,
            sort_order=len(placeholder.contentitems.filter(language_code=language)),
            **block['kwargs']
        )

        if 'items' in block:
            item_model = apps.get_model('cms', block['items']['model'])
            for item in block['items']['data']:
                if 'image' in item:
                    if item['image']:
                        response = requests.get(item['image'])
                        item['image'] = File(
                            File(response.raw, name=item['image'].split('/')[-1])
                        )
                    else:
                        print 'Missing image for: {}({})'.format(block_type, language)
                        del item['image']

                item_model.objects.create(
                    block=content_block,
                    **item
                )

        if 'migrate' in block:
            source = apps.get_model(*block['migrate']['source'].split('.'))
            target = apps.get_model(*block['migrate']['target'].split('.'))

            for source_object in source.objects.filter(
                language=language, **block['migrate']['filter']
            ):
                fields = dict(
                    (field, getattr(source_object, field)) for field
                    in block['migrate']['fields']
                )
                target.objects.create(
                    block=content_block,
                    **fields
                )

        if 'related' in block:
            source = apps.get_model(*block['related']['model'].split(':'))

            if 'slug' in block['related']:
                for slug in block['related']['slug']:
                    getattr(content_block, block['related']['field']).add(
                        source.objects.get(slug=slug)
                    )

            if 'id' in block['related']:
                for id in block['related']['id']:
                    getattr(content_block, block['related']['field']).add(
                        source.objects.get(id=id)
                    )

    def handle(self, *args, **options):
        if options['all']:
            tenants = Client.objects.all()

        if options['tenant']:
            tenants = [Client.objects.get(schema_name=options['tenant'])]

        for client in tenants:
            print "\n\nCreating homepage for {}".format(client.name)
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                ContentType.objects.clear_cache()

                (page, _created) = HomePage.objects.get_or_create(pk=1)
                languages = [lang[0] for lang in properties.LANGUAGES]

                for language_code in languages:
                    page.translations.get_or_create(
                        language_code=language_code,
                    )

                page_type = ContentType.objects.get_for_model(page)

                (placeholder, _created) = Placeholder.objects.get_or_create(
                    parent_id=page.pk,
                    parent_type_id=page_type.pk,
                    slot='content',
                    role='m'
                )
                for item in ContentItem.objects.filter(parent_id=page.pk, parent_type=page_type):
                    item.delete()

                for lang, blocks in properties.HOMEPAGE.items():
                    for (block_type, block) in blocks:
                        self.create_block(
                            block_type, block, placeholder, lang
                        )
