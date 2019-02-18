from rest_framework import serializers

from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import (
    get_resource_type_from_instance,
    get_resource_type_from_model
)

from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ImageSerializer
)
from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.utils.fields import SafeField
from bluebottle.utils.serializers import (
    ResourcePermissionField, FSMModelSerializer
)


class ThemeSerializer(ModelSerializer):
    class Meta:
        model = Theme
        fields = ('id', 'slug', 'name', 'description')


class RelatedField(serializers.BaseSerializer):
    def to_representation(self, data):
        return {
            'id': data.pk,
            'type': 'Initiative'
        }

    def to_internal_value(self, data):
        return Initiative.objects.get(pk=data['id'])


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()
    field = serializers.CharField()
    resource = RelatedField()

    def save(self):
        resource = self.validated_data['resource']
        transition = self.validated_data['transition']
        field = self.validated_data['field']

        transitions = getattr(
            resource,
            'get_available_{}_transitions'.format(field)
        )()

        if transition in [trans.name for trans in transitions]:
            getattr(resource, transition)()
            resource.save()
        else:
            import ipdb; ipdb.set_trace()

    class Meta:
        fields = ('id', 'transition', 'field', )
        resource_name = 'Transition'


class InitiativeSerializer(FSMModelSerializer):
    review_status = serializers.CharField(read_only=True)
    story = SafeField(required=False)
    slug = serializers.CharField(read_only=True)

    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    image = ImageSerializer(required=False)
    owner = ResourceRelatedField(read_only=True)
    reviewer = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))

    transitions = serializers.SerializerMethodField()

    def get_transitions(self, obj):
        result = {}
        for field in self.Meta.fsm_fields:
            result[field] = [
                transition.name for transition in
                getattr(obj, 'get_available_{}_transitions'.format(field))()
            ]

        return result

    included_serializers = {
        'owner': 'bluebottle.members.serializers.UserPreviewSerializer',
        'reviewer': 'bluebottle.members.serializers.UserPreviewSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta:
        model = Initiative
        fsm_fields = ['review_status']
        fields = (
            'id', 'title', 'review_status', 'categories', 'owner', 'reviewer', 'slug',
            'story', 'video_html', 'image', 'theme'
        )

        meta_fields = ('permissions', 'transitions')

    class JSONAPIMeta:
        included_resources = ['owner']
