from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DateParticipant,
    Interest,
)
from bluebottle.utils.serializers import ResourcePermissionField

ACTIVE_REGISTRATION_STATUSES = (
    'new',
    'accepted',
    'succeeded',
    'scheduled',
    'participating',
)
ACTIVE_PARTICIPANT_STATUSES = (
    'new',
    'accepted',
    'succeeded',
    'running',
)


class InterestSerializer(ModelSerializer):
    permissions = ResourcePermissionField('interest-detail', view_args=('pk',))
    user = ResourceRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    activity = ResourceRelatedField(queryset=Activity.objects.all())
    slot = ResourceRelatedField(
        queryset=DateActivitySlot.objects.all(),
        required=False,
        allow_null=True,
    )
    created = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Interest
        fields = (
            'id',
            'user',
            'activity',
            'slot',
            'permissions',
            'created',
        )
        meta_fields = ('permissions',)

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/interests'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
    }

    def _user_already_involved(self, user, activity, slot):
        if slot:
            return DateParticipant.objects.filter(
                user=user,
                slot=slot,
                status__in=ACTIVE_PARTICIPANT_STATUSES,
            ).exists()

        return activity.registrations.filter(
            user=user,
            status__in=ACTIVE_REGISTRATION_STATUSES,
        ).exists()

    def validate(self, data):
        request = self.context['request']
        user = data.get('user') or request.user
        activity = data.get('activity')
        slot = data.get('slot')

        if not activity:
            raise ValidationError({'activity': [_('This field is required.')]})

        activity = activity.get_real_instance()

        if isinstance(activity, DateActivity):
            if not slot:
                raise ValidationError(
                    {'slot': [_('A slot is required for date activities.')]}
                )
            if slot.activity_id != activity.id:
                raise ValidationError(
                    {'slot': [_('Slot does not belong to this activity.')]}
                )
            if slot.status != 'full':
                raise ValidationError(
                    _('Interests can only be registered for full slots.')
                )
        else:
            if slot:
                raise ValidationError(
                    {'slot': [_('Slot is only allowed for date activities.')]}
                )
            if activity.status != 'full':
                raise ValidationError(
                    _('Interests can only be registered for full activities.')
                )

        if self._user_already_involved(user, activity, slot):
            raise ValidationError(
                _('You are already participating in or applied to this activity.'),
                code='already_involved',
            )

        data['user'] = user
        data['activity'] = activity
        return data

    def create(self, validated_data):
        user = validated_data['user']
        activity = validated_data['activity']
        slot = validated_data.get('slot')

        if slot:
            interest, _created = Interest.objects.get_or_create(
                user=user,
                slot=slot,
                defaults={'activity': activity},
            )
        else:
            interest, _created = Interest.objects.get_or_create(
                user=user,
                activity=activity,
                slot=None,
            )
        return interest
