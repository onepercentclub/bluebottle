from rest_framework import serializers

from bluebottle.activities.utils import BaseContributionSerializer, BaseActivitySerializer, ActivityValidationSerializer
from bluebottle.assignments.filters import ApplicantListFilter
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.events.serializers import RegistrationDeadlineValidator, LocationValidator, LocationField
from bluebottle.geo.models import Geolocation
from bluebottle.utils.serializers import RelatedField, ResourcePermissionField, NonModelRelatedResourceField, \
    NoCommitMixin, FilteredRelatedField


class AssignmentValidationSerializer(ActivityValidationSerializer):
    start_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration = serializers.FloatField()
    registration_deadline = serializers.DateField(
        allow_null=True,
        validators=[RegistrationDeadlineValidator()]
    )
    is_online = serializers.BooleanField()
    location = LocationField(
        queryset=Geolocation.objects.all(),
        allow_null=True,
        validators=[LocationValidator()]
    )

    class Meta:
        model = Assignment
        fields = ActivityValidationSerializer.Meta.fields + (
            'start_date', 'start_time', 'is_online', 'location', 'duration',
            'registration_deadline',
        )

    class JSONAPIMeta:
        resource_name = 'activities/event-validations'


class AssignmentListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('assignment-detail', view_args=('pk',))
    validations = NonModelRelatedResourceField(AssignmentValidationSerializer)

    place = RelatedField(allow_null=True, queryset=Geolocation.objects.all())

    class Meta:
        model = Assignment
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline', 'registration_deadline',
            'capacity', 'expertise',
            'duration', 'place'

        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'place'
        ]
        resource_name = 'activities/assignments'


class AssignmentSerializer(NoCommitMixin, AssignmentListSerializer):
    contributions = FilteredRelatedField(many=True, filter_backend=ApplicantListFilter)

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


class ApplicantSerializer(BaseContributionSerializer):

    class Meta:
        model = Applicant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
