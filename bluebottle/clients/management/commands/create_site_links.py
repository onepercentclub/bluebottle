from StringIO import StringIO

from django.db import connection
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

import requests

from bluebottle.clients.models import Client
from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import (
    SiteLinks, LinkGroup, Link, LinkPermission, SitePlatformSettings
)
from bluebottle.utils.models import Language


class Command(BaseCommand):
    help = 'Create site links'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            action='store',
            dest='tenant',
            default=False,
            help='Create site links for specific tenant',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Create site links for all tenants',
        )

        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Overwrite site links if they already exist',
        )

    def _log(self, info, created):
        if created:
            label = 'created'
        else:
            label = 'exists'
        self.stdout.write(u'{} [{}]'.format(info, label))

    def _create_settings(self, settings):
        if 'footerPoweredBy' not in settings:
            settings['footerPoweredBy'] = '- Powered by:'

        if 'footerLink' in settings:
            if settings['footerLink'].startswith('http'):
                response = requests.get(settings['footerLink'])
                logo = StringIO(response.content)
            else:
                logo = StringIO(
                    settings['footerLink'].split(",")[1].decode('base64')
                )

            settings['footerLink'] = File(
                logo, name='logo.svg'
            )

        platform_settings, _created = SitePlatformSettings.objects.get_or_create()

        settings_map = {
            'footerPoweredBy': 'powered_by_text',
            'footerCopyrightLink': 'power_by_logo',
            'footerLinkTarget': 'powered_by_link',
            'footerLink': 'powered_by_logo',
            'email': 'contact_email',
            'phone': 'contact_phone',
            'copyright': 'copyright',
        }
        # handle a fixed list of settings
        for key, value in settings.items():
            try:
                setattr(platform_settings, settings_map[key], value)
            except KeyError:
                pass

        platform_settings.save()

    def _create_links(self, force):
        site_links = getattr(properties, 'SITE_LINKS', None)
        if site_links:
            # get languages
            LinkGroup.objects.all().delete()

            for key in site_links.keys():

                if key == 'settings':
                    self._create_settings(site_links['settings'])
                    continue

                lang_code = key
                try:
                    language = Language.objects.get(code=lang_code)
                except Language.DoesNotExist:
                    continue

                sl, created = SiteLinks.objects.get_or_create(language=language)

                lang_links = site_links[lang_code]
                sections = ['main', 'about', 'info', 'discover', 'social']

                for group_name in sections:
                    if group_name in lang_links:
                        group_links = lang_links[group_name]
                        lg, created = LinkGroup.objects.get_or_create(
                            name=group_name,
                            site_links=sl,
                            title=group_links.get('title', '')
                        )
                        self._log('Link Group called {}'.format(group_name), created)

                        for link in group_links['links']:
                            l, created = Link.objects.get_or_create(
                                link_group=lg,
                                highlight=link.get('highlight', False),
                                title=link.get('title', 'N/A'),
                                component=link.get('component', None),
                                component_id=link.get('component_id', None),
                                external_link=link.get('external_link', None)
                            )

                            self._log(u'  Link called {} created for {}'.format(link.get('title', 'N/A'), group_name),
                                      created)

                            perms = link.get('permissions', [])
                            for perm in perms:
                                p, created = LinkPermission.objects.get_or_create(permission=perm['permission'],
                                                                                  present=perm.get('present', True))

                                l.link_permissions.add(p)
                                self._log(u'    Permission called {} ({}) for {}'.format(
                                    perm['permission'],
                                    perm['present'],
                                    link.get('title', 'N/A')),
                                    created
                                )

    def handle(self, *args, **options):
        if options['all'] and options['tenant']:
            raise CommandError('--all and --tenant cannot be used together')

        if options['all']:
            tenants = Client.objects.all()
        else:
            tenants = Client.objects.filter(client_name=options['tenant'])

        for tenant in tenants:
            connection.set_tenant(tenant)
            with LocalTenant(tenant):
                self._create_links(options['force'])
