from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
    BaseActivityListSerializer)
from bluebottle.assignments.filters import ApplicantListFilter
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.permissions import ApplicantDocumentPermission
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField


class ApplicantDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'applicant-document'
    relationship = 'applicant_set'


class AssignmentListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('assignment-detail', view_args=('pk',))

    class Meta(BaseActivityListSerializer.Meta):
        model = Assignment
        fields = BaseActivityListSerializer.Meta.fields + (
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

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        included_resources = [
            'location',
            'expertise',
        ]
        resource_name = 'activities/assignments'

    included_serializers = dict(
        BaseActivityListSerializer.included_serializers,
        **{
            'expertise': 'bluebottle.tasks.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class AssignmentSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('assignment-detail', view_args=('pk',))
    contributions = FilteredRelatedField(many=True, filter_backend=ApplicantListFilter)

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
            'contributions',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'contributions.user',
            'contributions.document'
        ]
        resource_name = 'activities/assignments'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.tasks.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
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
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ApplicantDocumentPermission])

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
        'document': 'bluebottle.assignments.serializers.ApplicantDocumentSerializer',
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
