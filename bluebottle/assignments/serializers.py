from django.utils.translation import ugettext_lazy as _
from polymorphic.query import PolymorphicQuerySet
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
    ActivityValidationSerializer
)
from bluebottle.assignments.filters import ApplicantListFilter
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.permissions import ApplicantDocumentPermission
from bluebottle.events.serializers import LocationValidator, LocationField
from bluebottle.files.serializers import DocumentField, PrivateDocumentSerializer
from bluebottle.geo.models import Geolocation
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import RelatedField, ResourcePermissionField, NonModelRelatedResourceField, \
    FilteredRelatedField


class RegistrationDeadlineValidator(object):
    def set_context(self, field):
        self.end_date = field.parent.instance.end_date

    def __call__(self, value):
        if not self.end_date or value > self.end_date:
            raise serializers.ValidationError(
                _('Registration deadline should be before end date'),
                code='registration_deadline'
            )

        return value


class ApplicantDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'applicant-document'
    relationship = 'applicant_set'


class AssignmentValidationSerializer(ActivityValidationSerializer):
    end_date = serializers.DateField()
    duration = serializers.FloatField()
    registration_deadline = serializers.DateField(
        allow_null=True,
        validators=[RegistrationDeadlineValidator()]
    )
    is_online = serializers.BooleanField()
    end_date_type = serializers.CharField()
    location = LocationField(
        queryset=Geolocation.objects.all(),
        allow_null=True,
        validators=[LocationValidator()]
    )

    class Meta:
        model = Assignment
        fields = ActivityValidationSerializer.Meta.fields + (
            'end_date', 'end_date_type',
            'is_online', 'location', 'duration',
            'registration_deadline',
        )

    class JSONAPIMeta:
        resource_name = 'activities/assignment-validations'


class AssignmentListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('assignment-detail', view_args=('pk',))
    validations = NonModelRelatedResourceField(AssignmentValidationSerializer)

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
            'validations'
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
            'validations',
        ]
        resource_name = 'activities/assignments'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'expertise': 'bluebottle.tasks.serializers.SkillSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'document': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'validations': 'bluebottle.assignments.serializers.AssignmentValidationSerializer',
    }


class AssignmentSerializer(AssignmentListSerializer):
    contributions = FilteredRelatedField(many=True, filter_backend=ApplicantListFilter)
    location = RelatedField(allow_null=True, required=False, queryset=Geolocation.objects.all())

    class Meta(AssignmentListSerializer.Meta):
        fields = AssignmentListSerializer.Meta.fields + (
            'contributions',
        )

    class JSONAPIMeta(AssignmentListSerializer.JSONAPIMeta):
        included_resources = AssignmentListSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'contributions.user',
            'contributions.document'
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


class ApplicantDocumentField(DocumentField):

    def get_queryset(self):
        # Filter by permission
        # TODO: We might want to do this in a nicer way
        queryset = super(ApplicantDocumentField, self).get_queryset()
        request = self.context['request']
        permission = ApplicantDocumentPermission()
        parent = self.parent.instance
        # TODO: This is hideous! Please fix me.
        if isinstance(parent, PolymorphicQuerySet):
            parent = parent[0]
        if not permission.has_object_permission(request, self, parent):
            return queryset.none()
        return queryset

    def to_representation(self, value):
        # Return None if queryset is empty. Permission is denied.
        if not self.get_queryset():
            return None
        return super(ApplicantDocumentField, self).to_representation(value)


class ApplicantSerializer(BaseContributionSerializer):
    time_spent = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    motivation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    document = ApplicantDocumentField(required=False, allow_null=True)

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
