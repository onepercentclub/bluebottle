from builtins import object

from django.core.validators import URLValidator
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import format_field_names
from rest_framework_json_api.serializers import ModelSerializer, PolymorphicModelSerializer

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.cms.page_utils import apply_uploaded_image
from bluebottle.content.models import ContentBlock, ContentPage
from bluebottle.content.page_utils import BLOCK_TYPE_TO_RESOURCE
from bluebottle.files.models import Image
from bluebottle.utils.fields import PolymorphicSerializerMethodResourceRelatedField, SafeField
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import get_language_from_request


class BaseContentBlockSerializer(ModelSerializer):
    block_type = serializers.SerializerMethodField(read_only=True)

    def get_block_type(self, obj):
        return BLOCK_TYPE_TO_RESOURCE.get(obj.block_type, 'content/blocks/unknown')

    class Meta(object):
        model = ContentBlock
        fields = ('id', 'block_type')


class TitleBlockSerializer(BaseContentBlockSerializer):
    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('title_text', 'title_level')

    class JSONAPIMeta:
        resource_name = 'content/blocks/title'


class TextBlockSerializer(BaseContentBlockSerializer):
    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('text',)

    class JSONAPIMeta:
        resource_name = 'content/blocks/text'


class ImageBlockSerializer(BaseContentBlockSerializer):
    image = ImageSerializer()

    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('align', 'image')

    class JSONAPIMeta:
        resource_name = 'content/blocks/image'


class TextImageBlockSerializer(BaseContentBlockSerializer):
    image = ImageSerializer()

    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + (
            'text', 'image', 'ratio', 'align',
        )

    class JSONAPIMeta:
        resource_name = 'content/blocks/text-image'


class VideoBlockSerializer(BaseContentBlockSerializer):
    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('video_url', 'video_provider')

    class JSONAPIMeta:
        resource_name = 'content/blocks/video'


class ButtonBlockSerializer(BaseContentBlockSerializer):
    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('button_label', 'button_url')

    class JSONAPIMeta:
        resource_name = 'content/blocks/button'


class SpacerBlockSerializer(BaseContentBlockSerializer):
    class Meta(BaseContentBlockSerializer.Meta):
        fields = BaseContentBlockSerializer.Meta.fields + ('spacer_size',)

    class JSONAPIMeta:
        resource_name = 'content/blocks/spacer'


READ_SERIALIZERS = {
    'title': TitleBlockSerializer,
    'text': TextBlockSerializer,
    'image': ImageBlockSerializer,
    'text_image': TextImageBlockSerializer,
    'video': VideoBlockSerializer,
    'button': ButtonBlockSerializer,
    'spacer': SpacerBlockSerializer,
}


def serialize_content_block(instance, context=None):
    serializer_class = READ_SERIALIZERS.get(instance.block_type, TextBlockSerializer)
    attributes = serializer_class(instance, context=context or {}).data
    attributes.pop('id', None)
    attributes.pop('block_type', None)
    return {
        'type': BLOCK_TYPE_TO_RESOURCE[instance.block_type],
        'id': str(instance.pk),
        'attributes': format_field_names(attributes),
    }


class ContentBlockPolymorphicSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        TitleBlockSerializer,
        TextBlockSerializer,
        ImageBlockSerializer,
        TextImageBlockSerializer,
        VideoBlockSerializer,
        ButtonBlockSerializer,
        SpacerBlockSerializer,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poly_force_type_resolution = False

    @classmethod
    def get_polymorphic_serializer_for_instance(cls, instance):
        return READ_SERIALIZERS.get(instance.block_type, TextBlockSerializer)

    class Meta(object):
        model = ContentBlock


class TitleBlockWriteSerializer(ModelSerializer):
    class Meta(object):
        model = ContentBlock
        fields = ('title_text', 'title_level')

    class JSONAPIMeta:
        resource_name = 'content/blocks/title'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TextBlockWriteSerializer(ModelSerializer):
    text = SafeField(required=False, allow_blank=True)

    class Meta(object):
        model = ContentBlock
        fields = ('text',)

    class JSONAPIMeta:
        resource_name = 'content/blocks/text'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ImageBlockWriteSerializer(ModelSerializer):
    image = ResourceRelatedField(queryset=Image.objects.all(), required=False, allow_null=True)

    class Meta(object):
        model = ContentBlock
        fields = ('align', 'image')

    class JSONAPIMeta:
        resource_name = 'content/blocks/image'

    def update(self, instance, validated_data):
        uploaded_image = validated_data.pop('image', serializers.empty)
        if uploaded_image is not serializers.empty:
            if uploaded_image is None:
                instance.image.delete(save=False)
            else:
                apply_uploaded_image(instance, 'image', uploaded_image)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TextImageBlockWriteSerializer(ModelSerializer):
    text = SafeField(required=False, allow_blank=True)
    image = ResourceRelatedField(queryset=Image.objects.all(), required=False, allow_null=True)

    class Meta(object):
        model = ContentBlock
        fields = ('text', 'image', 'ratio', 'align')

    class JSONAPIMeta:
        resource_name = 'content/blocks/text-image'

    def update(self, instance, validated_data):
        uploaded_image = validated_data.pop('image', serializers.empty)
        if uploaded_image is not serializers.empty:
            if uploaded_image is None:
                instance.image.delete(save=False)
            else:
                apply_uploaded_image(instance, 'image', uploaded_image)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class VideoBlockWriteSerializer(ModelSerializer):
    class Meta(object):
        model = ContentBlock
        fields = ('video_url',)

    class JSONAPIMeta:
        resource_name = 'content/blocks/video'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


def validate_button_url(value):
    if not value or value.startswith('/'):
        return value

    URLValidator()(value)
    return value


class ButtonBlockWriteSerializer(ModelSerializer):
    button_url = serializers.CharField(
        allow_blank=True,
        max_length=500,
        required=False,
        validators=[validate_button_url],
    )

    class Meta(object):
        model = ContentBlock
        fields = ('button_label', 'button_url')

    class JSONAPIMeta:
        resource_name = 'content/blocks/button'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SpacerBlockWriteSerializer(ModelSerializer):
    class Meta(object):
        model = ContentBlock
        fields = ('spacer_size',)

    class JSONAPIMeta:
        resource_name = 'content/blocks/spacer'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


BLOCK_WRITE_SERIALIZERS = {
    'content/blocks/title': TitleBlockWriteSerializer,
    'content/blocks/text': TextBlockWriteSerializer,
    'content/blocks/image': ImageBlockWriteSerializer,
    'content/blocks/text-image': TextImageBlockWriteSerializer,
    'content/blocks/video': VideoBlockWriteSerializer,
    'content/blocks/button': ButtonBlockWriteSerializer,
    'content/blocks/spacer': SpacerBlockWriteSerializer,
}


class ContentPageWriteSerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    language = serializers.CharField(read_only=True)

    class Meta(object):
        model = ContentPage
        fields = (
            'id', 'title', 'slug', 'language', 'status', 'publication_date',
            'show_title', 'full_page',
        )

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data.setdefault('author', request.user)
        return super(ContentPageWriteSerializer, self).create(validated_data)

    def _language_from_request(self):
        request = self.context.get('request')
        if not request:
            return None
        return request.data.get('language') or get_language_from_request(request)

    def validate(self, attrs):
        language = None
        if self.instance:
            language = self.instance.language
        else:
            language = self._language_from_request()

        slug = attrs.get('slug')
        if slug and language:
            queryset = ContentPage.objects.filter(language=language, slug=slug)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    'slug': 'A page with this slug already exists for this language.',
                })

        return attrs

    class JSONAPIMeta:
        resource_name = 'content/pages'


class ContentPageListSerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    permissions = ResourcePermissionField('content-page-detail', view_args=('slug',))
    admin_url = serializers.SerializerMethodField()
    updated = serializers.DateTimeField(source='modification_date', read_only=True)

    def get_admin_url(self, obj):
        return obj.get_admin_url()

    class Meta(object):
        model = ContentPage
        fields = (
            'id', 'title', 'show_title', 'full_page', 'slug', 'language',
            'status', 'updated',
        )
        meta_fields = ('permissions', 'admin_url')

    class JSONAPIMeta:
        resource_name = 'content/pages'


class ContentPageSerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    blocks = PolymorphicSerializerMethodResourceRelatedField(
        ContentBlockPolymorphicSerializer,
        read_only=True,
        many=True,
        model=ContentBlock,
    )
    permissions = ResourcePermissionField('content-page-detail', view_args=('slug',))
    admin_url = serializers.SerializerMethodField()

    def get_blocks(self, obj):
        return obj.blocks.all()

    def get_admin_url(self, obj):
        return obj.get_admin_url()

    class Meta(object):
        model = ContentPage
        fields = (
            'id', 'title', 'show_title', 'full_page', 'slug', 'language',
            'status', 'publication_date', 'blocks',
        )
        meta_fields = ('permissions', 'admin_url')

    included_serializers = {
        'blocks': 'bluebottle.content.serializers.ContentBlockPolymorphicSerializer',
    }

    class JSONAPIMeta:
        resource_name = 'content/pages'
        included_resources = ['blocks']
