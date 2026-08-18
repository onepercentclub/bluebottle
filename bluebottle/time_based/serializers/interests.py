from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField,
    ResourceRelatedField,
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    Interest,
)
from bluebottle.time_based.serializers.interest_validators import (
    UserAlreadyInvolvedValidator,
)
from bluebottle.utils.serializers import ResourcePermissionField


class InterestSerializer(ModelSerializer):
    permissions = ResourcePermissionField('interest-detail', view_args=('pk',))
    user = ResourceRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    activity = PolymorphicResourceRelatedField(
        ActivitySerializer,
        queryset=Activity.objects.all(),
    )
    slot = ResourceRelatedField(
        queryset=DateActivitySlot.objects.all(),
        required=False,
        allow_null=True,
        default=None,
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
        validators = []

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/interests'
        included_resources = [
            'activity',
            'slot',
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
        'slot': 'bluebottle.time_based.serializers.serializers.DateActivitySlotSerializer',
    }

    def _existing_interest(self, user, activity, slot):
        if slot:
            return Interest.objects.filter(user=user, slot=slot).exists()

        return Interest.objects.filter(
            user=user,
            activity=activity,
            slot__isnull=True,
        ).exists()

    def validate(self, data):
        request = self.context['request']
        user = data.get('user') or request.user
        activity = data.get('activity')
        slot = data.get('slot')

        if not activity:
            raise ValidationError({'activity': [_('This field is required.')]})

        activity = activity.get_real_instance()
        already_interested = self._existing_interest(user, activity, slot)

        if isinstance(activity, DateActivity):
            if not slot:
                raise ValidationError(
                    {'slot': [_('A slot is required for date activities.')]}
                )
            if slot.activity_id != activity.id:
                raise ValidationError(
                    {'slot': [_('Slot does not belong to this activity.')]}
                )
            if not already_interested and (
                slot.status != 'full'
                or activity.status == 'registration_closed'
            ):
                raise ValidationError(
                    _('Interests can only be registered for full slots.')
                )
        else:
            if slot:
                raise ValidationError(
                    {'slot': [_('Slot is only allowed for date activities.')]}
                )
            if not already_interested and activity.status != 'full':
                raise ValidationError(
                    _('Interests can only be registered for full activities.')
                )

        UserAlreadyInvolvedValidator().validate(user, activity, slot)

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
            return interest

        interest, _created = Interest.objects.get_or_create(
            user=user,
            activity=activity,
            slot=None,
        )
        return interest
