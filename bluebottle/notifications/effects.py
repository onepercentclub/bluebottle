from django.utils.translation import ugettext_lazy as _
from bluebottle.fsm.effects import Effect


class BaseNotificationEffect(Effect):
    post_save = True

    def execute(self, send_messages=True, **kwargs):
        if send_messages:
            self.message(self.instance).compose_and_send()

    def __repr__(self):
        return '<Effect: Send {}>'.format(self.message)

    def __unicode__(self):
        message = self.message(self.instance)

        recipients = message.get_recipients()
        recipients_text = (u', ').join(recipient.email for recipient in recipients[:2])

        if len(recipients) > 2:
            recipients_text += u' (and {} more)'.format(len(recipients) - 2)

        return _('Message %s to %s') % (message.subject, recipients_text)


def NotificationEffect(_message):
    class _NotificationEffect(BaseNotificationEffect):
        message = _message

    return _NotificationEffect
