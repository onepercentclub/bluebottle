import dateutil
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    SerializerMethodResourceRelatedField
)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer, BaseContributorSerializer
)
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.time_based.serializers import RelatedLinkFieldByStatus
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import reverse_signed


class StartDateValidator():
    requires_context = True

    def __call__(self, value, serializer):
        parent = serializer.parent
        try:
            end = dateutil.parser.parse(parent.initial_data['end']).date()
        except (KeyError, TypeError):
            try:
                end = parent.instance.end
            except AttributeError:
                return

        if value and end and value > end:
            raise ValidationError('The activity should start before it ends')


class DeedSerializer(BaseActivitySerializer):
    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)

        if not instance or instance.status in ('draft', 'needs_work'):
            for key in self.fields:
                self.fields[key].allow_blank = True
                self.fields[key].validators = []
                self.fields[key].allow_null = True
                self.fields[key].required = False

    title = serializers.CharField()
    description = serializers.CharField()
    start = serializers.DateField(validators=[StartDateValidator()], allow_null=True)
    end = serializers.DateField(allow_null=True)

    permissions = ResourcePermissionField('deed-detail', view_args=('pk',))
    links = serializers.SerializerMethodField()

    my_contributor = SerializerMethodResourceRelatedField(
        model=DeedParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source='participants',
        related_link_view_name="related-deed-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "active": ["succeeded", "accepted"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )

    participants_export_url = PrivateFileSerializer(
        'deed-participant-export',
        url_args=('pk', ),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DeedParticipant).first()

    def get_links(self, instance):
        if instance.start and instance.end:
            return {
                'ical': reverse_signed('deed-ical', args=(instance.pk, )),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    class Meta(BaseActivitySerializer.Meta):
        model = Deed
        fields = BaseActivitySerializer.Meta.fields + (
            'my_contributor',
            'contributors',
            'start',
            'end',
            'enable_impact',
            'target',
            'links',
            'participants_export_url',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/deeds'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            "my_contributor",
            "my_contributor.user",
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.deeds.serializers.DeedParticipantSerializer',
            'my_contributor.user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class DeedListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('deed-detail', view_args=('pk',))

    class Meta(BaseActivityListSerializer.Meta):
        model = Deed
        fields = BaseActivityListSerializer.Meta.fields + (
            'start',
            'end',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/deeds'


class DeedTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Deed.objects.all())
    included_serializers = {
        'resource': 'bluebottle.deeds.serializers.DeedSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/deed-transitions'


class DeedParticipantSerializer(BaseContributorSerializer):
    activity = ResourceRelatedField(
        queryset=Deed.objects.all()
    )
    permissions = ResourcePermissionField('deed-participant-detail', view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        model = DeedParticipant
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ('permissions', )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/deeds/participants'
        included_resources = [
            "user",
            "user.avatar",
            "activity",
            "activity.goals",
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'user.avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
        'activity': 'bluebottle.deeds.serializers.DeedSerializer',
        'activity.goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
    }


class DeedParticipantListSerializer(DeedParticipantSerializer):
    pass


class DeedParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeedParticipant.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.deeds.serializers.DeedParticipantSerializer',
        'resource.activity': 'bluebottle.deeds.serializers.DeedSerializer',
        'resource.activity.goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'contributors/deeds/participant-transitions'
        included_resources = [
            'resource', 'resource.activity', 'resource.activity.goals'
        ]
