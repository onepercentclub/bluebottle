from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect


class BaseNotificationEffect(Effect):
    post_save = True
    title = _('Send email')
    template = 'admin/notification_effect.html'

    def execute(self, send_messages=True, **kwargs):
        if send_messages and self.is_valid:
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
            recipients_text = (', ').join(
                recipient.email for recipient in recipients[:2])

            if len(recipients) > 2:
                recipients_text += ' ' + \
                    _('(and {number} more)').format(
                        number=(len(recipients) - 2))
        except Exception:
            if message.get_recipients.__doc__:
                recipients_text = message.get_recipients.__doc__
            else:
                recipients_text = _('related users')
        return {'subject': message.generic_subject, 'recipients': recipients_text}

    def __unicode__(self):
        return _('Message {subject} to {recipients}').format(**self._content())

    @property
    def is_valid(self):
        return (
            all([condition(self.instance) for condition in self.conditions]) and
            self.message(self.instance).get_recipients()
        )

    def to_html(self):
        return _('Message <em>{subject}</em> to {recipients}').format(**self._content())

    @property
    def description(self):
        return '"{}"'.format(self.message(self.instance).generic_subject)

    @property
    def help(self):
        message = self.message(self.instance)
        recipients = message.get_recipients()
        recipients_text = ', '.join(
            recipient.email for recipient in recipients[:2])

        if len(recipients) > 2:
            recipients_text += ' (and {} more)'.format(len(recipients) - 2)

        return _('to {}').format(recipients_text)

    @property
    def content(self):
        return self.message.generic_content

    @property
    def subject(self):
        return self.message.generic_subject


def NotificationEffect(message, conditions=None):
    _message = message
    _conditions = conditions

    class _NotificationEffect(BaseNotificationEffect):
        message = _message
        conditions = _conditions or []

    return _NotificationEffect
