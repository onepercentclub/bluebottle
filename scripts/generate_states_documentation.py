import requests
from django.conf import settings
from django.utils.module_loading import import_string

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.fsm.utils import document_model, document_notifications
from scripts.generate_notifications_documentation import generate_notification_html

api = settings.CONFLUENCE['api']


def make_list(source):
    return "<ul>{}</ul>".format("".join(["<li>{}</li>".format(el) for el in source]))


def make_table_head(source):
    return "<tr>{}</tr>".format("".join(["<th>{}</th>".format(el.capitalize()) for el in source]))


def make_row(source):
    row = "<tr>"
    for k, el in source.items():
        if isinstance(el, list):
            el = make_list(el)
        row += "<td>{}</td>".format(el)
    row += "</tr>"
    return row


def make_table(source, layout='default'):
    table = "<table data-layout=\"{}\">".format(layout)
    table += make_table_head(source[0].keys())
    for row in source:
        table += make_row(row)
    table += "</table>"
    return table


def generate_html(documentation):
    html = ""
    html += "<h2>States</h2>"
    html += "<em>All states this instance can be in.</em>"
    html += make_table(documentation['states'])

    html += "<h2>Transitions</h2>"
    html += "<em>An instance will always move from one state to the other through a transition. " \
            "A manual transition is initiated by a user. An automatic transition is initiated by the system, " \
            "either through a trigger or through a side effect of a related object.</em>"
    html += make_table(documentation['transitions'], layout='full-width')

    if len(documentation['triggers']):
        html += "<h2>Triggers</h2>"
        html += "<em>These are events that get triggered when the instance changes, " \
                "other then through a transition. " \
                "Mostly it would be triggered because a property changed (e.g. a deadline).</em>"
        html += make_table(documentation['triggers'], layout='full-width')

    if len(documentation['periodic_tasks']):
        html += "<h2>Periodic tasks</h2>"
        html += "<em>These are events that get triggered when certain dates are passed. " \
                "Every 15 minutes the system checks for passing deadlines, registration dates and such.</em>"
        html += make_table(documentation['periodic_tasks'], layout='full-width')

    return html


def run(*args):

    if 'prod' in args:
        models = settings.CONFLUENCE['prod_models']
    else:
        models = settings.CONFLUENCE['dev_models']

    tenant = Client.objects.get(schema_name=settings.CONFLUENCE['tenant'])

    with LocalTenant(tenant):
        for model in models:
            url = "{}/wiki/rest/api/content/{}".format(api['domain'], model['page_id'])
            response = requests.get(url, auth=(api['user'], api['key']))
            data = response.json()
            version = data['version']['number'] + 1
            documentation = document_model(import_string(model['model']))
            html = generate_html(documentation)
            messages = document_notifications(import_string(model['model']))
            if len(messages):
                html += "<h2>Automated messages</h2>"
                html += "<em>On some triggers automated e-mails are send.</em>"
                html += generate_notification_html(messages)
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
                        "value": html.encode('ascii', 'ignore'),
                        "representation": "storage"
                    }
                }
            }
            url += '?expand=body.storage'
            response = requests.put(url, json=data, auth=(api['user'], api['key']))
            if response.status_code == 200:
                print("[OK] {}".format(model['title']))
            else:
                print("[ERROR] {}".format(model['title']))
