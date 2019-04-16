from bluebottle.notifications.adapters import BaseMessageAdapter
from bluebottle.utils.email_backend import send_mail


class EmailMessageAdapter(BaseMessageAdapter):

    @property
    def template_name(self):
        return 'mails/{}'.format(self.message.template)

    def send(self):
        send_mail(
            template_name=self.template_name,
            subject=self.message.subject,
            to=self.message.recipient,
            obj=self.message.content_object
        )
