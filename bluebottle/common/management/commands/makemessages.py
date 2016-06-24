import json
import codecs
import tempfile
from django.core.management.commands.makemessages import Command as BaseCommand


class Command(BaseCommand):
    """ Extend the makemessages to include some of the fixtures """

    fixtures = [
        ('bb_projects', 'project_data.json'),
        ('bb_tasks', 'skills.json'),
        ('geo', 'geo_data.json'),
    ]

    def handle(self, *args, **kwargs):
        strings = []
        for app, file in self.fixtures:
            with open('bluebottle/{}/fixtures/{}'.format(app, file)) as fixture_file:
                strings += [fixture['fields']['name'].encode('utf-8') for fixture in json.load(fixture_file)]

        with tempfile.NamedTemporaryFile(dir='bluebottle', suffix='.py') as temp:
            temp.write('\n'.join(['gettext("{}")'.format(string) for string in strings]))
            temp.flush()

            return super(Command, self).handle(*args, **kwargs)
