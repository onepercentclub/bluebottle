import sys
from StringIO import StringIO

import requests
from django.core.management import call_command
from django.conf import settings

models = [
    {
        'title': 'Funding - Donation',
        'model': 'bluebottle.funding.models.Donation',
        'page_id': '739999825'
    }
]

api = settings.CONFLUENCE['api']


def run(*args):

    for model in models:
        url = "{}/wiki/rest/api/content/{}".format(api['domain'], model['page_id'])
        response = requests.get(url, auth=(api['user'], api['key']))
        data = response.json()
        version = data['version']['number'] + 1
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        call_command('print_transitions', model['model'])
        sys.stdout = old_stdout
        md = result.getvalue()

        md = u"<ac:structured-macro ac:name=\"markdown\" ac:schema-version=\"1\" " \
             u"data-layout=\"full-width\" ac:macro-id=\"68e06823-d52b-444a-b606-59d728ce0124\">" \
             u"<ac:plain-text-body><![CDATA[{}]]></ac:plain-text-body></ac:structured-macro>".format(md)

        data = {
            "id": model['page_id'],
            "type": "page",
            "status": "current",
            "title": model['title'],
            "version": {
                "number": version
            },
            "body": {
                "storage": {
                    "value": md,
                    "representation": "storage"
                }
            }
        }
        url += '?expand=body.storage'
        response = requests.put(url, json=data, auth=(api['user'], api['key']))
        if response.status_code == 200:
            print "[OK] {}".format(model['title'])
        else:
            print "[ERROR] {}".format(model['title'])
