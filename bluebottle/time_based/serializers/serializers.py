from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    HyperlinkedRelatedField, SerializerMethodHyperlinkedRelatedField

)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.utils import BaseContributionSerializer
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField, CurrentStatusField
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.models import TimeContribution, DateActivitySlot, Skill
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.time_based.serializers import RelatedLinkFieldByStatus
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import reverse_signed


class UnreviewedContributorsField(SerializerMethodHyperlinkedRelatedField):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super().__init__(*args, **kwargs)

    def get_url(self, *args, **kwargs):
        url = super().get_url(*args, **kwargs)

        if url:
            return f"{url}?filter[status]=new"


class ActivitySlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField('date-slot-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    status = FSMField(read_only=True)
    location = ResourceRelatedField(queryset=Geolocation.objects, required=False, allow_null=True)
    current_status = CurrentStatusField(source='states.current_state')
    timezone = serializers.SerializerMethodField()

    participants_export_url = PrivateFileSerializer(
        'date-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_timezone(self, instance):
        is_online = getattr(instance, 'is_online', False)
        has_location = getattr(instance, 'location', False)
        return instance.location.timezone if not is_online and has_location else None

    class Meta:
        fields = (
            'id',
            'activity',
            'start',
            'end',
            'transitions',
            'is_online',
            'timezone',
            'location_hint',
            'online_meeting_url',
            'location',
            'participants_export_url'
        )
        meta_fields = (
            'status',
            'current_status',
            'contributor_count',
            'permissions',
            'transitions',
            'required',
            'errors',
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'activity',
            'location',
            'my_contributor',
        ]

    included_serializers = {
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }


class DateActivitySlotSerializer(ActivitySlotSerializer):
    participants = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name='date-slot-related-participants',
        related_link_url_kwarg='slot_id',
        include_my=True,
        statuses={
            "active": ["accepted", "succeeded", "running"],
            "failed": ["failed", "rejected", "expired", "cancelled"],
        },
    )

    errors = ValidationErrorsField()
    required = RequiredErrorsField()
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('slot-ical', args=(instance.pk,)),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    def get_root_meta(self, resource, many):
        if many:
            try:
                activity_id = self.context['request'].GET['activity']
                queryset = self.context['view'].queryset.filter(
                    activity_id=int(activity_id)
                ).order_by('start')

                try:
                    contributor_id = self.context['request'].GET['contributor']
                    queryset = queryset.filter(
                        participants__status__in=['registered', 'succeeded'],
                        participants__participant_id=contributor_id
                    )
                except KeyError:
                    pass

                first = queryset.first()
                return {
                    'first': first.start if first else None,
                    'total': len(queryset),
                }
            except (KeyError, ValueError):
                pass

        return {}

    class Meta(ActivitySlotSerializer.Meta):
        model = DateActivitySlot
        fields = ActivitySlotSerializer.Meta.fields + (
            'title',
            'start',
            'links',
            'duration',
            'capacity',
            'participants',
        )

    class JSONAPIMeta(ActivitySlotSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/date-slots'
        included_resources = [
            'activity',
            'my_contributor',
            'my_contributor.user',
            'location',
            'location.country'
        ]

    included_serializers = dict(
        ActivitySlotSerializer.included_serializers.serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'country': 'bluebottle.geo.serializers.CountrySerializer',
        }
    )


class ParticipantsField(HyperlinkedRelatedField):
    def __init__(self, many=True, read_only=True, *args, **kwargs):
        super().__init__(
            many=many,
            read_only=read_only,
            related_link_view_name='period-participants',
            related_link_url_kwarg='activity_id',
        )


class DateSlotTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateActivitySlot.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/slot-transitions'


class TimeContributionSerializer(BaseContributionSerializer):
    permissions = ResourcePermissionField('time-contribution-detail', view_args=('pk',))

    class Meta(BaseContributionSerializer.Meta):
        model = TimeContribution
        fields = BaseContributionSerializer.Meta.fields + ("contribution_type", "start")
        meta_fields = BaseContributionSerializer.Meta.meta_fields + ("permissions",)

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-contributions'


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta(object):
        model = Skill
        fields = ('id', 'name', 'expertise')

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'skills'
