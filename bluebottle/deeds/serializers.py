from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer
)
from bluebottle.deeds.models import Deed
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import (
    DateParticipant
)
from bluebottle.utils.serializers import ResourcePermissionField


class DeedSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))
    # my_contributor = SerializerMethodResourceRelatedField(
    #     model=DateParticipant,
    #     read_only=True,
    #     source='get_my_contributor'
    # )
    #
    # contributors = FilteredRelatedField(
    #     many=True,
    #     filter_backend=ParticipantListFilter,
    #     related_link_view_name='deed-participants',
    #     related_link_url_kwarg='activity_id'
    #
    # )

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DateParticipant).first()

    class Meta(BaseActivitySerializer.Meta):
        model = Deed
        fields = BaseActivitySerializer.Meta.fields + (
            # 'contributors',
            'start',
            'end'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/deeds'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            # 'my_contributor',
            # 'my_contributor.contributions',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        # **{
        #     'my_contributor': 'bluebottle.deeds.serializers.DeedParticipantSerializer',
        #     'my_contributor.contributions': 'bluebottle.deeds.serializers.DeedContributionSerializer',
        # }
    )


class DeedTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Deed.objects.all())
    included_serializers = {
        'resource': 'bluebottle.deeds.serializers.DeedSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/deed-transitions'
