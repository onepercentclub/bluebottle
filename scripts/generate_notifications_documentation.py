import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.module_loading import import_string

from bluebottle.fsm.utils import document_notifications

api = settings.CONFLUENCE['api']


def clean_text(content):
    return '\n'.join([
        line.strip() for line
        in content.strip().split('\n')
        if line.strip() and line.strip() not in ['-------------------', '-  -']
    ])


def clean_html(content):
    soup = BeautifulSoup(content, "html")
    for elem in soup.find_all(['html', 'body', 'table', 'tbody', 'tr', 'td', 'th', 'center']):
        elem.unwrap()
    soup.head.extract()
    soup.contents[0].extract()
    return clean_text(str(soup))


def generate_notification_html(documentation):
    html = ""
    for message in documentation:
        html += """
        <table>
        <colgroup>
        <col style='width: 150px;' />
        <col style='width: 650x;' />
        </colgroup>
        <tr><th>Trigger</th><td>{}</td></tr>
        <tr><th>Description</th><td>{}</td></tr>
        <tr><th>Class</th><td>{}</td></tr>
        <tr><th>Template</th><td>{}</td></tr>
        <tr><th>To</th><td>{}</td></tr>
        <tr><th>Subject</th><td>{}</td></tr>
        </table>
        <blockquote>{}</blockquote>
        """.format(
            message['trigger'],
            message['description'],
            message['class'],
            message['template'],
            message['recipients'],
            message['subject'],
            clean_text(message['content_text'])
        )
    return html


def run(*args):
    if 'prod' in args:
        models = settings.CONFLUENCE['prod_models']
        notifications = settings.CONFLUENCE['prod_notifications']
    else:
        models = settings.CONFLUENCE['dev_models']
        notifications = settings.CONFLUENCE['dev_notifications']

    url = "{}/wiki/rest/api/content/{}".format(api['domain'], notifications['page_id'])
    response = requests.get(url, auth=(api['user'], api['key']))
    data = response.json()
    version = data['version']['number'] + 1
    html = ''

    for model in models:
        model_class = import_string(model['model'])
        messages = document_notifications(model_class)
        if len(messages):
            html += "<h2>{}</h2>".format(model_class._meta.verbose_name)
            html += generate_notification_html(messages)

    data = {
        "id": notifications['page_id'],
        "type": "page",
        "status": "current",
        "title": notifications['title'],
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
        print("[OK]")
    else:
        print("[ERROR]")
