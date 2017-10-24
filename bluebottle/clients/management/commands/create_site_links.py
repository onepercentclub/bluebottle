import json

from django.db import connection
from django.core.management.base import BaseCommand, CommandError

from bluebottle.clients.models import Client
from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SiteLinks, LinkGroup, Link, LinkPermission
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

    def _create_links(self, force):
        def _log(info, created):
            if created:
                label = 'created'
            else:
                label = 'exists'
            print('{} [{}]'.format(info, label))

        site_links = getattr(properties, 'SITE_LINKS', None)
        if site_links:
            # get languages
            for lang_code in site_links.keys():
                language = Language.objects.get(code=lang_code)
                sl, created = SiteLinks.objects.get_or_create(language=language)

                lang_links = site_links[lang_code]
                for group_name in lang_links.keys():
                    if group_name in ['main', 'about', 'info', 'discover', 'social']:
                        group_links = lang_links[group_name]
                        lg, created = LinkGroup.objects.get_or_create(name=group_name,
                                                                      site_links=sl,
                                                                      title=group_links.get('title', ''))
                        _log('Link Group called {}'.format(group_name), created)

                        for link in group_links['links']:
                            l, created = Link.objects.get_or_create(link_group=lg,
                                                                    highlight=link.get('highlighted', False),
                                                                    title=link.get('title', 'N/A'),
                                                                    component=link.get('component', None),
                                                                    component_id=link.get('component_id', None),
                                                                    external_link=link.get('external_link', None))

                            _log('  Link called {} created for {}'.format(link.get('title', 'N/A'), group_name),
                                 created)

                            perms = link.get('permissions', [])
                            for perm in perms:
                                p, created = LinkPermission.objects.get_or_create(permission=perm['permission'],
                                                                                  present=perm.get('present', True))

                                l.link_permissions.add(p)
                                _log('    Permission called {} ({}) for {}'.format(perm['permission'], perm['present'],
                                                                                   link.get('title', 'N/A')), created)

    def handle(self, *args, **options):
        if options['all'] and options['tenant']:
            raise CommandError('--all and --tenant cannot be used together')

        if options['all']:
            tenants = Client.objects.all()
        else:
            tenants = Client.objects.filter(client_name=options['tenant'])

        success = []
        for tenant in tenants:
            connection.set_tenant(tenant)
            with LocalTenant(tenant):
                self._create_links(options['force'])

                success += [
                    {
                        'name': tenant.client_name,
                    }
                ]

        self.stdout.write(json.dumps(success, indent=4))
