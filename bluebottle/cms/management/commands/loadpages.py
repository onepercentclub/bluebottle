# -*- coding: utf-8 -*-
import json

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from fluent_contents.models import Placeholder, ContentItem

from bluebottle.utils.models import Language


class Command(BaseCommand):
    help = 'Load content pages from json'

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', type=str, default=None, action='store')
        parser.add_argument('--quiet', '-q', action='store_true')

    def create_block(self, block, placeholder):
        model = apps.get_model(block['app'], block['model'])
        content_type = ContentType.objects.get_for_model(model)

        content_block = model.objects.create_for_placeholder(
            placeholder,
            polymorphic_ctype=content_type,
            **block['fields']
        )

        if 'items' in block:
            for item in block['items']:
                item_model = apps.get_model(item['app'], item['model'])
                item_model.objects.create(
                    block=content_block,
                    **item['data']
                )

    def handle(self, *args, **options):
        try:
            with open(options['file']) as json_file:
                data = json.load(json_file)
            quiet = options['quiet']
            for page_data in data:

                if page_data['model'] == 'Page':
                    if not quiet:
                        self.stdout.write(
                            'Loading {} {}'.format(page_data['model'], page_data['properties']['title'])
                        )
                    model = apps.get_model(page_data['app'], page_data['model'])
                    language = Language.objects.get(code=page_data['properties']['language'])
                    # Make publication_date tz aware
                    page_data['properties']['publication_date'] += '+00:00'
                    page, _c = model.objects.get_or_create(
                        language=language,
                        slug=page_data['properties']['slug'],
                        defaults=page_data['properties']
                    )
                    page_type = ContentType.objects.get_for_model(page)
                    slot = 'blog_contents'
                else:
                    if not quiet:
                        self.stdout.write(
                            'Loading {}'.format(page_data['model'])
                        )
                    model = apps.get_model(page_data['app'], page_data['model'])
                    page, _c = model.objects.get_or_create(
                        defaults=page_data['properties']
                    )
                    page_type = ContentType.objects.get_for_model(page)
                    slot = 'content'

                (placeholder, _created) = Placeholder.objects.get_or_create(
                    parent_id=page.pk,
                    parent_type_id=page_type.pk,
                    slot=slot,
                    role='m'
                )

                for item in ContentItem.objects.filter(parent_id=page.pk, parent_type=page_type):
                    item.delete()

                for block in page_data['data']:
                    self.create_block(
                        block, placeholder
                    )
        except FileNotFoundError:
            print(f"File not found {options['file']}")
