from StringIO import StringIO

import requests
import sys
from django.conf import settings
from django.core.management import call_command

apps = [
    {
        'title': 'Notifications - Initiatives',
        'app': 'bluebottle.initiatives',
        'page_id': '833192092'
    },
    {
        'title': 'Notifications - Activities',
        'app': 'bluebottle.activities',
        'page_id': '961773675'
    },
    {
        'title': 'Notifications - Tasks',
        'app': 'bluebottle.assignments',
        'page_id': '830701653'
    },
    {
        'title': 'Notifications - Events',
        'app': 'bluebottle.events',
        'page_id': '833192109'
    },
    {
        'title': 'Notifications - Funding',
        'app': 'bluebottle.funding',
        'page_id': '833192116'
    },
]

api = settings.CONFLUENCE['api']


def run(*args):
    for app in apps:
        url = "{}/wiki/rest/api/content/{}".format(api['domain'], app['page_id'])
        response = requests.get(url, auth=(api['user'], api['key']))
        data = response.json()
        version = data['version']['number'] + 1
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        call_command('print_notifications', app['app'])
        sys.stdout = old_stdout
        html = result.getvalue()
        html = html.encode('ascii', 'ignore')

        data = {
            "id": app['page_id'],
            "type": "page",
            "status": "current",
            "title": app['title'],
            "version": {
                "number": version
            },
            "body": {
                "storage": {
                    "value": html,
                    "representation": "storage"
                }
            }
        }
        url += '?expand=body.storage'
        response = requests.put(url, json=data, auth=(api['user'], api['key']))
        if response.status_code == 200:
            print "[OK] {}".format(app['title'])
        else:
            print "[ERROR] {}".format(app['title'])
            print response.content
