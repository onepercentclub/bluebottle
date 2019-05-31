from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.notifications.models import Message


class TransitionMessage(object):
    subject = 'Status changed'
    template = 'messages/base'
    context = {}

    def __init__(self, obj):
        self.obj = obj

    def __unicode__(self):
        return self.subject

    def get_template(self):
        return self.template

    def get_subject(self, language=None):
        if not language:
            language = properties.LANGUAGE_CODE
        with TenantLanguage(language):
            context = {}
            for key, item in self.context.items():
                context[key] = getattr(self.obj, item)
            return self.subject.format(**context)

    def get_messages(self):
        return [
            Message(
                template=self.get_template(),
                subject=self.get_subject(recipient.primary_language),
                content_object=self.obj,
                recipient=recipient
            ) for recipient in self.get_recipients()
        ]

    def get_recipients(self):
        return [self.obj.owner]

    def compose_and_send(self):
        for message in self.get_messages():
            message.save()
            message.send()
