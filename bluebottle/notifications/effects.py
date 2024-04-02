import logging

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible

from bluebottle.fsm.effects import Effect

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseNotificationEffect(Effect):
    title = _('Send email')
    template = 'admin/notification_effect.html'

    def post_save(self, **kwargs):
        if self.options.get('send_messages', True) and self.is_valid:
            message = self.message(
                self.instance,
                custom_message=self.options.get('message'),
                **self.options
            )
            if self.message.delay and self.message.task_id:
                message.send_delayed()
            else:
                message.compose_and_send()

    def __repr__(self):
        return '<Effect: Send {}>'.format(self.message)

    def _content(self):
        message = self.message(self.instance)

        try:
            recipients = message.get_recipients()
            recipients_text = (u', ').join(
                recipient.email for recipient in recipients[:2])

            if len(recipients) > 2:
                recipients_text += u' ' + \
                    _('(and {number} more)').format(
                        number=(len(recipients) - 2))
        except Exception:
            if message.get_recipients.__doc__:
                recipients_text = message.get_recipients.__doc__
            else:
                recipients_text = _('related users')
        return {'subject': message.generic_subject, 'recipients': recipients_text}

    def __str__(self):
        return _('Message {subject} to {recipients}').format(**self._content())

    @property
    def is_valid(self):
        return (
            all([condition(self) for condition in self.conditions]) and
            len(self.message(self.instance, **self.options).get_recipients()) > 0
        )

    def to_html(self):
        return _('Message <em>{subject}</em> to {recipients}').format(**self._content())

    @property
    def description(self):
        return '"{}"'.format(self.message(self.instance).generic_subject)

    @classmethod
    def render(cls, effects):
        message = effects[0].message(effects[0].instance)
        recipients = [
            recipient.email for effect in effects
            for recipient in effect.message(effect.instance).get_recipients()
        ]

        context = {
            'opts': effects[0].instance.__class__._meta,
            'effects': effects,
            'subject': message.generic_subject,
            'recipients': recipients
        }
        return render_to_string(cls.template, context)

    @property
    def help(self):
        message = self.message(self.instance)
        recipients = message.get_recipients()
        recipients_text = u', '.join(
            recipient.email for recipient in recipients[:2])

        if len(recipients) > 2:
            recipients_text += u' (and {} more)'.format(len(recipients) - 2)

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


class BaseLogErrorEffect(Effect):
    title = _('Raise error')
    template = 'admin/notification_effect.html'

    def get_args(self):
        return {
            'title': self.instance.title
        }

    def post_save(self, **kwargs):
        if self.is_valid:
            logger.error(self.message.format(**self.get_args()))

    def __repr__(self):
        return '<Effect: Raise error {}>'.format(self.message)

    def __str__(self):
        return 'Raise error "{}"'.format(self.message)

    @property
    def is_valid(self):
        return (
            all([condition(self) for condition in self.conditions]) and
            self.message
        )

    def to_html(self):
        return 'Raise error "{}"'.format(self.message)

    @property
    def description(self):
        return 'Raise error "{}"'.format(self.message)

    @property
    def help(self):
        return 'Raise error "{}"'.format(self.message)


def LogErrorEffect(message, conditions=None):
    _message = message
    _conditions = conditions

    class _LogErrorEffect(BaseLogErrorEffect):
        message = _message
        conditions = _conditions or []

    return _LogErrorEffect
