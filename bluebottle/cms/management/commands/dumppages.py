import json

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import (
    HomePage,
)
from bluebottle.pages.models import Page


class Command(BaseCommand):
    help = 'Dump content pages to json'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', '-s', action='store', dest='tenant',
                            help="The tenant to dump pages for")
        parser.add_argument('--file', '-f', type=str, default=None, action='store')

    def _get_fields(self, block):
        fields = block.__dict__
        skip_fields = [
            'id', '_state', 'parent_type_id', 'parent_id',
            'polymorphic_ctype_id', 'contentitem_ptr_id',
            'placeholder_id', 'block_id', 'order_field',
            'order_field_name', '_block_cache']
        for field in skip_fields:
            if field in fields:
                del fields[field]
        return fields

    def _dump(self, page):
        data = []
        for block in page.content.get_content_items():
            items = []
            if hasattr(block, 'items'):
                for item in block.items.all():
                    items.append({
                        'model': item.__class__.__name__,
                        'app': item.__class__._meta.app_label,
                        'data': self._get_fields(item)
                    })
            fields = self._get_fields(block)
            data.append({
                'model': block.__class__.__name__,
                'app': block.__class__._meta.app_label,
                'fields': fields,
                'items': items
            })
        return data

    def handle(self, *args, **options):
        client = Client.objects.get(schema_name=options['tenant'])

        print "Dumping pages for {}".format(client.name)

        with LocalTenant(client, clear_tenant=True):
            ContentType.objects.clear_cache()
            data = []
            page = HomePage.objects.get(pk=1)

            data.append({
                'model': 'HomePage',
                'app': 'cms',
                'properties': {},
                'data': self._dump(page)
            })

            for page in Page.objects.all():
                data.append({
                    'model': 'Page',
                    'app': 'pages',
                    'properties': {
                        'title': page.title,
                        'slug': page.slug,
                        'status': page.status,
                        'language': page.language,
                        'full_page': page.full_page,
                        'publication_date': now().strftime('%Y-%m-%d %H:%M')
                    },
                    'data': self._dump(page)
                })
            if options['file']:
                text_file = open(options['file'], "w")
                text_file.write(json.dumps(data))
                text_file.close()
            else:
                print json.dumps(data)
