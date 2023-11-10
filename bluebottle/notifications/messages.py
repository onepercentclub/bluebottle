# -*- coding: utf-8 -*-
from builtins import object
from builtins import str
from operator import attrgetter
from functools import partial
import logging

import icalendar
from celery import shared_task

from django.db import connection

from django.core.cache import cache
from django.contrib.admin.options import get_content_type_for_model
from django.template import loader
from django.utils.html import format_html
from future.utils import python_2_unicode_compatible

from bluebottle.clients import properties

from bluebottle.notifications.models import Message, MessageTemplate
from bluebottle.utils import translation
from bluebottle.utils.utils import get_current_language, to_text


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
    event_data = None
    send_once = False
    delay = None

    def __reduce__(self):
        return (partial(self.__class__, self.obj, **self.options), ())

    @property
    def task_id(self):
        return f'{self.__class__.__name__}-{self.obj.id}'

    def get_generic_context(self):
        language = get_current_language()
        context = {
            'obj': self.obj,
            'site': 'https://[site domain]',
            'site_name': '[site name]',
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

    def get_content_html(self, recipient):
        context = self.get_context(recipient)
        template = loader.get_template("mails/{}.html".format(self.template))
        return template.render(context)

    def get_content_text(self, recipient):
        return to_text.handle(self.get_content_html(recipient))

    def get_calendar_attachement(self):
        event = self.event_data
        cal = icalendar.Calendar()
        event_item = icalendar.Event()
        event_item.add('summary', event['summary'])
        event_item.add('organizer', event['organizer'])
        event_item.add('description', event['description'])
        event_item.add('url', event['url'])
        event_item.add('location', event['location'])
        event_item.add('dtstart', event['start_time'])
        event_item.add('dtend', event['end_time'])
        cal.add_component(event_item)
        ical_data = cal.to_ical()
        return ('event.ics', ical_data, 'text/calendar')

    def get_context(self, recipient):
        from bluebottle.clients.utils import tenant_url, tenant_name
        context = {
            'site': tenant_url(),
            'site_name': tenant_name(),
            'language': recipient.primary_language,
            'contact_email': properties.CONTACT_EMAIL,
            'recipient_name': recipient.first_name,
            'first_name': recipient.first_name,
            'action_link': getattr(self, 'action_link', None),
            'action_title': getattr(self, 'action_title', None)
        }
        for key, item in list(self.context.items()):
            try:
                context[key] = attrgetter(item)(self.obj)
            except AttributeError:
                context[key] = None

        if 'context' in self.options:
            context.update(self.options['context'])

        if self.event_data:
            context['attachments'] = [self.get_calendar_attachement()]

        return context

    def __init__(self, obj, **options):
        self.obj = obj
        self.options = options

    def __str__(self):
        return self.subject

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

                context = self.get_context(recipient, **base_context)
                subject = str(self.subject.format(**context))

                body_html = None
                body_txt = None

                if not custom_message and custom_template:
                    custom_template.set_current_language(recipient.primary_language)
                    try:
                        subject = custom_template.subject.format(**context)
                        body_html = format_html(custom_template.body_html, **context)
                        body_txt = custom_template.body_txt.format(**context)
                    except custom_template.DoesNotExist:
                        # Translation for current language not set, use default.
                        pass

                yield Message(
                    template=self.get_template(),
                    subject=subject,
                    content_object=self.obj,
                    recipient=recipient,
                    body_html=body_html,
                    body_txt=body_txt,
                    bcc=self.get_bcc_addresses(),
                    custom_message=custom_message
                )

    def get_recipients(self):
        """the owner"""
        return [self.obj.owner]

    def get_bcc_addresses(self):
        return []

    def compose_and_send(self, **base_context):
        for message in self.get_messages(**base_context):
            context = self.get_context(message.recipient, **base_context)
            message.save()

            message.send(**context)

    @property
    def is_delayed(self):
        return cache.get(self.task_id)

    def send_delayed(self):
        cache.set(self.task_id, True, self.delay)

        compose_and_send.apply_async(
            [self, connection.tenant],
            countdown=self.delay,
            task_id=self.task_id
        )


@shared_task
def compose_and_send(message, tenant):
    from bluebottle.clients.utils import LocalTenant

    with LocalTenant(tenant, clear_tenant=True):
        try:
            message.compose_and_send()
        except Exception as e:
            print('!!!!!', e)
            logger.error(e)
