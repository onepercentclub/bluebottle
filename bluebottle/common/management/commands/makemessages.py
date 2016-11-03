import json
import tempfile

from django.core.management.commands.makemessages import Command as BaseCommand

from bluebottle.clients.utils import get_currencies


class Command(BaseCommand):
    """ Extend the makemessages to include some of the fixtures """

    fixtures = [
        ('bb_projects', 'project_data.json'),
        ('bb_tasks', 'skills.json'),
        ('geo', 'geo_data.json'),
    ]

    def handle(self, *args, **kwargs):
        with tempfile.NamedTemporaryFile(dir='bluebottle', suffix='.py') as temp:
            for app, file in self.fixtures:
                with open('bluebottle/{}/fixtures/{}'.format(app, file)) as fixture_file:
                    strings = [
                        fixture['fields']['name'].encode('utf-8')
                        for fixture
                        in json.load(fixture_file)
                    ]

                    for string in strings:
                        temp.write('gettext("{}")\n'.format(string))

            for currency in get_currencies():
                temp.write('gettext("{}")\n'.format(currency['name']))

            temp.flush()

            return super(Command, self).handle(*args, **kwargs)
