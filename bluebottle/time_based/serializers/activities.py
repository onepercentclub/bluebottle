from rest_framework import serializers
from rest_framework_json_api.relations import (
    SerializerMethodHyperlinkedRelatedField, ResourceRelatedField
)

from bluebottle.activities.utils import BaseActivitySerializer
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.time_based.models import DeadlineActivity, DeadlineParticipant, DeadlineRegistration
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.fsm.serializers import TransitionSerializer


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['permissions'] = ResourcePermissionField(self.detail_view_name, view_args=('pk',))
        self.fields['contributors'] = SerializerMethodHyperlinkedRelatedField(
            model=self.participant_model,
            read_only=True,
            many=True,
            related_link_view_name=self.related_participant_view_name,
            related_link_url_kwarg='activity_id'
        )
        self.fields['registrations'] = SerializerMethodHyperlinkedRelatedField(
            model=self.registration_model,
            read_only=True,
            many=True,
            related_link_view_name=self.related_registration_view_name,
            related_link_url_kwarg='activity_id'
        )

        self.fields['participants_export_url'] = PrivateFileSerializer(
            self.export_view_name,
            url_args=('pk',),
            filename='participant.csv',
            permission=CanExportParticipantsPermission,
            read_only=True
        )

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'registration_deadline',
            'expertise',
            'review',
            'registration_flow',
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',
            'contributors',
            'registration_flow',
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',
            'permissions',
            'registrations'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
        }
    )


class DeadlineActivitySerializer(TimeBasedBaseSerializer):
    participant_model = DeadlineParticipant
    registration_model = DeadlineRegistration
    detail_view_name = 'deadline-detail'
    related_participant_view_name = 'deadline-participants'
    related_registration_view_name = 'related-deadline-registrations'
    export_view_name = 'deadline-participant-export'

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DeadlineActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'is_online',
            'location',
            'location_hint',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/deadlines'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DeadlineTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/deadline-transitions'
        included_resources = ['resource', ]
