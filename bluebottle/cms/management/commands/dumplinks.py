from __future__ import print_function
import json

from django.core.management.base import BaseCommand

from bluebottle.cms.models import (
    SiteLinks)


class Command(BaseCommand):
    help = 'Dump site links to json'

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', type=str, default=None, action='store')

    def handle(self, *args, **options):
        data = []
        for site_links in SiteLinks.objects.all():
            groups = []
            for group in site_links.link_groups.all():
                links = []
                for link in group.links.all():
                    links.append({
                        'title': link.title,
                        'highlight': link.highlight,
                        'open_in_new_tab': link.open_in_new_tab,
                        'link': link.link,
                        'link_order': link.link_order
                    })
                groups.append({
                    'name': group.name,
                    'title': group.title,
                    'group_order': group.group_order,
                    'links': links
                })

            data.append({
                'language': site_links.language.code,
                'has_copyright': site_links.has_copyright,
                'groups': groups

            })
        if options['file']:
            text_file = open(options['file'], "w")
            text_file.write(json.dumps(data, indent=2))
            text_file.close()
        else:
            print(json.dumps(data))
