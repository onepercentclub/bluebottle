import requests

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.utils.translation import gettext_lazy as _

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.events.models import Event, Webhook
from bluebottle.events.views import EventListView
from bluebottle.events.serializers import EventSerializer
from bluebottle.updates.models import Update
from bluebottle.fsm.effects import Effect

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request


class BaseTriggerEventEffect(Effect):
    title = _('Trigger event')
    template = 'admin/notification_effect.html'

    def post_save(self):
        event = Event(event_type=self.event_type, content_object=self.instance)

        event.save()

    def __str__(self):
        return _(f'Trigger {self.event_type}')


def TriggerEvent(event_type, conditions=None):
    _event_type = event_type
    _conditions = conditions

    class _TriggerEventEffect(BaseTriggerEventEffect):
        event_type = _event_type
        conditions = _conditions or []

    return _TriggerEventEffect


class BaseCreateUpdateEffect(Effect):
    title = _('Create wallpost for event')
    template = 'admin/notification_effect.html'

    @property
    def is_valid(self):
        return super().is_valid and self.instance.event_type in self.event_types


class CreateContributionUpdateEffect(BaseCreateUpdateEffect):
    event_types = ['donation.succeeded', 'deed-participant.succeeded']

    def post_save(self):
        content_object = self.instance.content_object

        update = Update(
            author=content_object.user,
            event=self.instance,
            activity=content_object.activity
        )
        update.save()


class CreateActivityUpdateEffect(BaseCreateUpdateEffect):
    event_types = [
        'deed.published',
        'deed.succeeded',
        'funding.approved',
        'funding.succeeded',
        'funding.50%',
        'funding.100%',
    ]

    def post_save(self):
        content_object = self.instance.content_object

        update = Update(
            author=content_object.owner,
            event=self.instance,
            activity=content_object
        )
        update.save()


class EventWebhookEffect(Effect):
    template = 'admin/event_webhook.html'

    def post_save(self):
        context = {
            'view': EventListView(),
            'request': Request(APIRequestFactory().get('/'))
        }
        serializer = EventSerializer(instance=self.instance, context=context)

        renderer = BluebottleJSONAPIRenderer()
        data = renderer.render(
            serializer.data,
            'application/vnd.api+json',
            context
        )

        for hook in Webhook.objects.all():
            requests.post(
                hook.url,
                data=data,
                headers={
                    'Content-Type': 'application/vnd.api+json'
                }
            )


class SendEventEffect(Effect):
    template = 'admin/send_event.html'

    def post_save(self):
        instance = self.instance
        channel_layer = get_channel_layer()
        serializer = EventSerializer(instance)
        async_to_sync(channel_layer.group_send)(
            "events",
            {
                "type": "send_event",
                "instance": serializer.data,
            }
        )
