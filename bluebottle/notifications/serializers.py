import json
from builtins import object
from string import Formatter

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import PolymorphicResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.notifications.activity_messages import get_activity_actions
from bluebottle.notifications.models import NotificationPlatformSettings, ActivityMessageTemplate
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.serializers import ResourcePermissionField


class NotificationPlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = NotificationPlatformSettings

        fields = (
            'share_options',
            'facebook_at_work_url',
        )


ALLOWED_PLACEHOLDERS = (
    'title', 'first_name', 'recipient_name', 'applicant_name',
    'site_name', 'contact_email', 'start', 'end', 'duration',
)


def validate_placeholders(value):
    try:
        fields = [field for _text, field, _spec, _conv in Formatter().parse(value) if field is not None]
    except ValueError:
        raise ValidationError(_('Invalid use of curly braces.'))

    invalid = [field for field in fields if field not in ALLOWED_PLACEHOLDERS]
    if invalid:
        raise ValidationError(
            _('Unknown placeholder(s): {invalid}. Allowed: {allowed}').format(
                invalid=', '.join('{%s}' % field for field in invalid),
                allowed=', '.join('{%s}' % field for field in ALLOWED_PLACEHOLDERS),
            )
        )
    return value


class ActivityMessageTemplateSerializer(ModelSerializer):
    permissions = ResourcePermissionField('activity-message-template-detail', view_args=('pk',))
    activity = PolymorphicResourceRelatedField(
        ActivitySerializer,
        queryset=Activity.objects.all(),
    )
    subject = serializers.CharField(
        max_length=200, allow_blank=True, required=False, validators=[validate_placeholders]
    )
    body = RichTextField(source='body_html', allow_blank=True, required=False)

    def validate_body(self, value):
        validate_placeholders(json.loads(value)['html'])
        return value

    def validate(self, data):
        activity = data.get('activity', getattr(self.instance, 'activity', None))
        action = data.get('action', getattr(self.instance, 'action', None))

        if self.instance and activity != self.instance.activity:
            raise ValidationError({'activity': _('The activity can not be changed.')})

        if action not in get_activity_actions(activity):
            raise ValidationError({'action': _('This message can not be customised for this activity.')})

        return data

    class Meta:
        model = ActivityMessageTemplate
        fields = (
            'id',
            'activity',
            'action',
            'insert_method',
            'subject',
            'body',
            'permissions',
            'created',
            'updated',
        )
        read_only_fields = ('created', 'updated')
        meta_fields = ('permissions',)
        validators = [
            UniqueTogetherValidator(
                queryset=ActivityMessageTemplate.objects.all(),
                fields=('activity', 'action'),
                message=_('There already is a custom message for this action on this activity.')
            )
        ]

    class JSONAPIMeta:
        resource_name = 'activity-message-templates'


class ActivityMessageDefaultSerializer(serializers.Serializer):
    id = serializers.CharField()
    action = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField()
    action_title = serializers.CharField()

    class JSONAPIMeta:
        resource_name = 'activity-message-defaults'
