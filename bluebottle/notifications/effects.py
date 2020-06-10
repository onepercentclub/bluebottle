from django.utils.translation import ugettext_lazy as _
from bluebottle.fsm.effects import Effect


class BaseNotificationEffect(Effect):
    post_save = True
    title = _('Send email')

    def execute(self, send_messages=True):
        if send_messages:
            self.message(
                self.instance,
                custom_message=self.options.get('message')
            ).compose_and_send()

    def __repr__(self):
        return '<Effect: Send {}>'.format(self.message)

    def _content(self):
        message = self.message(self.instance)

        try:
            recipients = message.get_recipients()
            recipients_text = (u', ').join(recipient.email for recipient in recipients[:2])

            if len(recipients) > 2:
                recipients_text += u' ' + _('(and {number} more)').format(number=(len(recipients) - 2))
        except Exception:
            if message.get_recipients.__doc__:
                recipients_text = message.get_recipients.__doc__
            else:
                recipients_text = _('related users')
        return {'subject': message.generic_subject, 'recipients': recipients_text}

    def __unicode__(self):
        return _('Message {subject} to {recipients}').format(**self._content())

    def to_html(self):
        return _('Message <em>{subject}</em> to {recipients}').format(**self._content())

    @property
    def description(self):
        return '"{}"'.format(self.message(self.instance).generic_subject)

    @property
    def help(self):
        message = self.message(self.instance)
        recipients = message.get_recipients()
        recipients_text = (u', ').join(recipient.email for recipient in recipients[:2])

        if len(recipients) > 2:
            recipients_text += u' (and {} more)'.format(len(recipients) - 2)

        return _('to {}').format(recipients_text)

    @property
    def content(self):
        return self.message.generic_content

    @property
    def subject(self):
        return self.message.generic_subject


def NotificationEffect(_message):

    class _NotificationEffect(BaseNotificationEffect):
        message = _message

    return _NotificationEffect
