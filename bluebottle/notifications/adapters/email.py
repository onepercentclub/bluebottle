from bluebottle.notifications.adapters import BaseMessageAdapter
from bluebottle.utils.email_backend import send_mail


class EmailMessageAdapter(BaseMessageAdapter):

    @property
    def template_name(self):
        return 'mails/{}'.format(self.message.template)

    def send(self, **context):
        send_mail(
            template_name=self.template_name,
            subject=self.message.subject,
            to=self.message.recipient,
            obj=self.message.content_object,
            custom_message=self.message.custom_message,
            body_html=self.message.body_html,
            body_txt=self.message.body_txt,
            **context
        )
