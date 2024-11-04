# -*- coding: utf-8 -*-
import json

from django.core.management.base import BaseCommand

from bluebottle.cms.models import SiteLinks, LinkGroup, Link
from bluebottle.utils.models import Language


class Command(BaseCommand):
    help = 'Load site links from json'

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', type=str, default=None, action='store')

    def handle(self, *args, **options):
        try:
            with open(options['file']) as json_file:
                data = json.load(json_file)

            for site_links in data:
                lang = Language.objects.filter(code=site_links['language']).first()
                if lang:
                    sl, _created = SiteLinks.objects.update_or_create(
                        language=lang,
                        defaults={
                            'has_copyright': site_links['has_copyright']
                        }
                    )
                    for group in site_links['groups']:
                        lg, _created = LinkGroup.objects.update_or_create(
                            site_links=sl,
                            name=group['name'],
                            defaults={
                                'title': group['title'],
                                'group_order': group['group_order']
                            }
                        )
                        for link in group['links']:
                            Link.objects.update_or_create(
                                link_group=lg,
                                link=link['link'],
                                defaults={
                                    'open_in_new_tab': link['open_in_new_tab'],
                                    'title': link['title'],
                                    'link_order': link['link_order'],
                                    'highlight': link['highlight']
                                }
                            )
        except FileNotFoundError:
            print(f"File not found {options['file']}")
