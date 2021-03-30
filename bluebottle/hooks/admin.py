from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext as _

from django_singleton_admin.admin import SingletonAdmin

from bluebottle.hooks.models import WebHook, SlackSettings, SignalLog

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@admin.register(WebHook)
class WebHookAdmin(admin.ModelAdmin):
    readonly_fields = ['secret_key']


@admin.register(SignalLog)
class SignalLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'instance', 'event')


@admin.register(SlackSettings)
class SlackSettingsAdmin(SingletonAdmin):
    def save_model(self, request, obj, form, change):
        client = WebClient(token=obj.token)

        try:
            joined_channels = [
                channel['name'] for
                channel in client.users_conversations().data['channels']
            ]
            public_channels = [
                channel for
                channel in client.conversations_list().data['channels']
            ]

            for channel_name in obj.channels:
                if channel_name[1:] not in joined_channels:
                    channel_id = next(
                        (channel['id'] for channel in public_channels if channel['name'] == channel_name[1:]),
                        None
                    )
                    if channel_id:
                        client.conversations_join(channel=channel_id)
                    else:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            _((
                                '{} is not a public channel. Please add this bot to the app in the slack'
                                ' interface'
                            ).format(channel_name))
                        )

        except SlackApiError as e:
            if e.response.data['error'] == 'invalid_auth':
                message = _('Invalid Slack authentication token')
            else:
                message = _('Slack error: {}').format(e.response['data']['error'])

            messages.add_message(
                request,
                messages.ERROR,
                message
            )

        super().save_model(request, obj, form, change)
