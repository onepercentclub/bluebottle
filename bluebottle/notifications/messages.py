from bluebottle.notifications.models import Message


class TransitionMessage(object):
    subject = 'Status changed'
    template = 'messages/base'

    def __init__(self, obj):
        self.obj = obj

    def __unicode__(self):
        return self.subject

    def get_template(self):
        return self.template

    def get_messages(self):
        return [
            Message(
                template=self.get_template(),
                subject=self.subject,
                content_object=self.obj,
                recipient=recipient
            ) for recipient in self.get_recipients()
        ]

    def get_recipients(self):
        return [self.obj.owner]

    def compose_and_send(self):
        for message in self.get_messages():
            message.send()
            message.save()
