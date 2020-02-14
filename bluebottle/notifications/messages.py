# -*- coding: utf-8 -*-
from operator import attrgetter

from django.contrib.admin.options import get_content_type_for_model
from django.db import connection
from django.utils import translation
from django.utils.html import format_html

from bluebottle.clients import properties
from bluebottle.notifications.models import Message, MessageTemplate


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

    def get_context(self, recipient):
        from bluebottle.clients.utils import tenant_url
        tenant = connection.tenant
        context = {
            'site': tenant_url(),
            'site_name': tenant.name,
            'language': recipient.primary_language,
            'contact_email': properties.CONTACT_EMAIL,
            'first_name': recipient.first_name
        }
        for key, item in self.context.items():
            context[key] = attrgetter(item)(self.obj)

        if 'context' in self.options:
            context.update(self.options['context'])

        return context

    def __init__(self, obj, **options):
        self.obj = obj
        self.options = options

    def __unicode__(self):
        return self.subject

    def get_template(self):
        return self.template

    def get_message_template(self):
        path = "{}.{}".format(self.__module__, self.__class__.__name__)
        return MessageTemplate.objects.filter(message=path).first()

    def get_messages(self, once=False):
        custom_message = self.options.get('custom_message', '')
        custom_template = self.get_message_template()
        recipients = list(set(self.get_recipients()))
        for recipient in recipients:
            with translation.override(recipient.primary_language):
                if once:
                    try:
                        Message.objects.get(
                            template=self.get_template(),
                            recipient=recipient,
                            content_type=get_content_type_for_model(self.obj),
                            object_id=self.obj.pk
                        )
                        continue
                    except Message.DoesNotExist:
                        pass

                context = self.get_context(recipient)
                subject = unicode(self.subject.format(**context))

                body_html = None
                body_txt = None

                if not custom_message and custom_template:
                    custom_template.set_current_language(recipient.primary_language)
                    try:
                        subject = custom_template.subject.format(**context)
                        body_html = format_html(custom_template.body_html.format(**context))
                        body_txt = custom_template.body_txt.format(**context)
                    except custom_template.DoesNotExist:
                        # Translation for current lagnuage not set, use default.
                        pass

                yield Message(
                    template=self.get_template(),
                    subject=subject,
                    content_object=self.obj,
                    recipient=recipient,
                    body_html=body_html,
                    body_txt=body_txt,
                    custom_message=custom_message
                )

    def get_recipients(self):
        return [self.obj.owner]

    def compose_and_send(self, once=False):
        for message in self.get_messages(once=once):
            context = self.get_context(message.recipient)
            message.save()
            message.send(**context)
