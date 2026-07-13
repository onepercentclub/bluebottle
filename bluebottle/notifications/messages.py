# -*- coding: utf-8 -*-
import logging
from builtins import object
from builtins import str
from functools import partial
from operator import attrgetter

from django.contrib.admin.options import get_content_type_for_model
from django.core.cache import cache
from django.db import connection
from django.template import loader
from django.utils import translation as django_translation
from django.utils.html import format_html
from future.utils import python_2_unicode_compatible

from bluebottle.celery import app
from bluebottle.clients import properties
from bluebottle.mails.models import MailPlatformSettings
from bluebottle.notifications.models import Message, MessageTemplate
from bluebottle.utils import translation
from bluebottle.utils.utils import get_current_language, to_text, get_tenant_name

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class TransitionMessage(object):
    """
    Base model for sending message
    When the subject contains a variable it should be specified in context, e.g.
    subject = "Un update on {initiative_title}"
    context = {'initiative_title': 'title'}
    The value is taken as an attribute of the related object (self.obj).
    So in the example if the transition is on initiative it wil be `initiative.title`.
    """
    subject = 'Status changed'
    template = 'messages/base'
    context = {}
    send_once = False
    delay = None

    def __reduce__(self):
        return (partial(self.__class__, self.obj, **self.options), ())

    @property
    def task_id(self):
        return f'{self.__class__.__name__}-{self.obj.id}'

    @property
    def action_link(self):
        return ''

    def get_generic_context(self):
        language = get_current_language()
        context = {
            'obj': self.obj,
            'site': 'https://[site domain]',
            'site_name': get_tenant_name(),
            'language': language,
            'contact_email': '[platform manager email]',
            'recipient_name': '[first name]',
        }
        for key, item in list(self.context.items()):
            try:
                context[key] = attrgetter(item)(self.obj)
            except AttributeError:
                logger.error(f'Missing attribute in message context: {item}')
                context[key] = item

        if 'context' in self.options:
            context.update(self.options['context'])
        return context

    @property
    def generic_subject(self):
        context = self.get_generic_context()
        return str(self.subject.format(**context))

    @property
    def generic_content(self):
        context = self.get_generic_context()
        template = loader.get_template("mails/{}.html".format(self.template))
        return template.render(context)

    @property
    def generic_content_html(self):
        context = self.get_generic_context()
        template = loader.get_template("mails/{}.html".format(self.template))
        return template.render(context)

    @property
    def generic_content_text(self):
        return to_text.handle(self.generic_content_html)

    def get_content_html(self, recipient, obj=None):
        django_translation.activate(recipient.primary_language)
        context = self.get_context(recipient)
        if obj:
            context['obj'] = obj
        template = loader.get_template("mails/{}.html".format(self.template))
        return template.render(context)

    def get_content_text(self, recipient):
        return to_text.handle(self.get_content_html(recipient))

    def get_first_recipient(self):
        recipients = list(filter(None, self.get_recipients()))
        return recipients[0] if recipients else None

    def get_message_block_html(self, recipient=None):
        if recipient is None:
            recipient = self.get_first_recipient()

        if recipient:
            with translation.override(recipient.primary_language):
                django_translation.activate(recipient.primary_language)
                context = self.get_context(recipient)
                custom_template = self.get_message_template()
                if custom_template:
                    custom_template.set_current_language(recipient.primary_language)
                    try:
                        return str(format_html(custom_template.body_html.html, **context))
                    except custom_template.DoesNotExist:
                        pass
                return self._render_message_block_html(context)

        return self._render_message_block_html(self.get_generic_context())

    def get_message_block_text(self, recipient=None):
        if recipient is None:
            recipient = self.get_first_recipient()
        return to_text.handle(self.get_message_block_html(recipient)).strip()

    def get_default_custom_message(self, recipient=None):
        return self.get_message_block_text(recipient)

    def _render_message_block_html(self, context):
        context = dict(context)
        context['only_message'] = True
        template = loader.get_template("mails/{}.html".format(self.template))
        return template.render(context)

    def attachments(self, recipients):
        pass

    def get_context(self, recipient):
        from bluebottle.clients.utils import tenant_url, tenant_name
        context = {
            "site": tenant_url(),
            "site_name": tenant_name(),
            "language": recipient.primary_language,
            "contact_email": properties.CONTACT_EMAIL,
            "recipient_name": recipient.first_name,
            "first_name": recipient.first_name,
            "action_link": self.get_action_link(recipient),
            "action_title": getattr(self, "action_title", None),
            "utm_campaign": self.__class__.__name__,
        }
        for key, item in list(self.context.items()):
            try:
                context[key] = attrgetter(item)(self.obj)
            except AttributeError:
                context[key] = None
            except Exception as e:
                __import__('ipdb').set_trace()
                print(e)

        if 'context' in self.options:
            context.update(self.options['context'])

        attachments = self.attachments(recipient)
        if attachments:
            context['attachments'] = attachments
        return context

    def get_action_link(self, recipient):
        return getattr(self, "action_link", None)

    def __init__(self, obj, **options):
        self.obj = obj
        self.options = options

    def __str__(self):
        return self.subject

    @property
    def reply_to(self):
        mail_settings = MailPlatformSettings.load()
        return mail_settings.reply_to

    def get_template(self):
        return self.template

    def get_message_template(self):
        path = "{}.{}".format(self.__module__, self.__class__.__name__)
        return MessageTemplate.objects.filter(message=path).first()

    def already_send(self, recipient):
        return Message.objects.filter(
            template=self.get_template(),
            recipient=recipient,
            content_type=get_content_type_for_model(self.obj),
            object_id=self.obj.pk
        ).count() > 0

    def get_messages(self, **base_context):
        custom_message = self.options.get('custom_message', '')
        custom_template = self.get_message_template()
        recipients = list(set(self.get_recipients()))
        for recipient in filter(None, recipients):
            with translation.override(recipient.primary_language):
                if self.send_once and self.already_send(recipient):
                    continue

                # Explicitly activate language to force lazy translation evaluation
                django_translation.activate(recipient.primary_language)
                context = self.get_context(recipient, **base_context)
                # Force evaluation of lazy translation string in correct language context
                subject = str(self.subject).format(**context)

                body_html = None
                insert_method = 'append'

                if not custom_message and custom_template:
                    custom_template.set_current_language(recipient.primary_language)
                    try:
                        # Force language activation for custom template formatting
                        django_translation.activate(recipient.primary_language)
                        subject = custom_template.subject.format(**context)
                        body_html = format_html(custom_template.body_html.html, **context)
                        insert_method = custom_template.insert_method
                    except custom_template.DoesNotExist:
                        # Translation for current language not set, use default.
                        pass

                yield Message(
                    insert_method=insert_method,
                    template=self.get_template(),
                    subject=subject,
                    content_object=self.obj,
                    recipient=recipient,
                    body_html=body_html,
                    bcc=self.get_bcc_addresses(),
                    custom_message=custom_message
                )

    def get_recipients(self):
        """the owner"""
        return [self.obj.owner]

    def get_bcc_addresses(self):
        return []

    def compose_and_send(self, **base_context):
        if self.obj.pk:
            self.obj.refresh_from_db()
        for message in self.get_messages(**base_context):
            context = self.get_context(message.recipient, **base_context)
            reply_to = self.reply_to
            if reply_to:
                context['reply_to'] = reply_to
            message.save()

            message.send(**context)

    @property
    def is_delayed(self):
        return cache.get(self.task_id)

    def send_delayed(self):
        from django.conf import settings

        cache.set(self.task_id, True, self.delay)

        if getattr(settings, 'TESTING', False):
            compose_and_send(self, connection.tenant)
            return

        compose_and_send.apply_async(
            [self, connection.tenant],
            countdown=self.delay,
            task_id=self.task_id,
        )


@app.task
def compose_and_send(message, tenant):
    from bluebottle.clients.utils import LocalTenant

    with LocalTenant(tenant, clear_tenant=True):
        try:
            message.compose_and_send()
        except Exception:
            logger.exception(
                'Error sending delayed notification %s for %s',
                message.__class__.__name__,
                getattr(message.obj, 'pk', message.obj),
            )
            raise
