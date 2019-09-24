from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
)
from bluebottle.assignments.filters import ApplicantListFilter
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.files.serializers import DocumentField, DocumentSerializer
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField


class ApplicantDocumentSerializer(DocumentSerializer):
    content_view_name = 'initiative-image'
    relationship = 'applicant_set'


class AssignmentListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('assignment-detail', view_args=('pk',))

    class Meta(BaseActivitySerializer.Meta):
        model = Assignment
        fields = BaseActivitySerializer.Meta.fields + (
            'is_online',
            'end_date',
            'end_date_type',
            'registration_deadline',
            'capacity',
            'expertise',
            'duration',
            'location',
            'permissions',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'location',
            'expertise',
            'initiative',
            'initiative.image',
            'initiative.location',
            'initiative.place',
        ]
        resource_name = 'activities/assignments'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'expertise': 'bluebottle.tasks.serializers.SkillSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class AssignmentSerializer(AssignmentListSerializer):
    contributions = FilteredRelatedField(many=True, filter_backend=ApplicantListFilter)

    class Meta(AssignmentListSerializer.Meta):
        fields = AssignmentListSerializer.Meta.fields + (
            'contributions',
        )

    class JSONAPIMeta(AssignmentListSerializer.JSONAPIMeta):
        included_resources = AssignmentListSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'contributions.user'
        ]

    included_serializers = dict(
        AssignmentListSerializer.included_serializers,
        **{
            'contributions': 'bluebottle.assignments.serializers.ApplicantSerializer',
        }
    )


class AssignmentTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Assignment.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.assignments.serializers.AssignmentSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'assignment-transitions'


class ApplicantSerializer(BaseContributionSerializer):
    time_spent = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    motivation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    document = DocumentField(required=False, allow_null=True)

    class Meta(BaseContributionSerializer.Meta):
        model = Applicant
        fields = BaseContributionSerializer.Meta.fields + (
            'time_spent',
            'motivation',
            'document'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=Applicant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/applicants'
        included_resources = [
            'user',
            'activity',
            'document'
        ]

    included_serializers = {
        'activity': 'bluebottle.assignments.serializers.AssignmentSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'document': 'bluebottle.files.serializers.DocumentSerializer',
    }


class ApplicantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Applicant.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.assignments.serializers.ApplicantSerializer',
        'resource.activity': 'bluebottle.assignments.serializers.AssignmentSerializer',
    }

    class JSONAPIMeta:
        resource_name = 'contributions/applicant-transitions'
        included_resources = [
            'resource',
            'resource.activity',
        ]
