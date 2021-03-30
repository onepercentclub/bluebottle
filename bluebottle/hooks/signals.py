import uuid

from collections import namedtuple

import requests

from django.dispatch import receiver, Signal
from django.utils.translation import ugettext as _
from django.utils.timezone import now

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer

from bluebottle.activities.models import Activity

from bluebottle.hooks.serializers import (
    ContributorWebHookSerializer, ActivityWebHookSerializer
)
from bluebottle.hooks.models import WebHook, SignalLog, SlackSettings

from slack_sdk import WebClient


hook = Signal()

Hook = namedtuple('Hook', ['pk', 'event', 'created', 'instance'])


@receiver(hook)
def send_webhook(sender, event=None, instance=None, **kwargs):
    model = Hook(event=event, instance=instance, pk=str(uuid.uuid4()), created=now())

    if isinstance(instance, Activity):
        serializer_class = ActivityWebHookSerializer
    else:
        serializer_class = ContributorWebHookSerializer

    data = BluebottleJSONAPIRenderer().render(
        serializer_class(model).data,
        renderer_context={'view': serializer_class.JSONAPIMeta}
    )

    for hook in WebHook.objects.all():
        try:
            requests.post(hook.url, data=data)
        except requests.RequestException:
            pass


@receiver(hook)
def save_hook(sender, event=None, instance=None, **kwargs):
    SignalLog.objects.create(
        event=event,
        instance=instance
    )


@receiver(hook)
def send_slack_message(sender, event=None, instance=None, **kwargs):
    settings = SlackSettings.objects.first()
    if settings:
        client = WebClient(token=settings.token)

        if event == 'accepted':
            message = _('{} joined "{}"'.format(instance.user.first_name, instance.activity.title))
        elif event == 'approved':
            message = _('A new activity "{}" was added'.format(instance.title))

        if message:
            client.chat_postMessage(
                channel='#dev-devops-bots', text=message
            )
