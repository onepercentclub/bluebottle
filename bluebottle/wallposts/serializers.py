from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from rest_framework import serializers

from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, PolymorphicSerializer, ContentTextField, PhotoSerializer)
from bluebottle.utils.model_dispatcher import get_project_model, get_fundraiser_model

from .models import (
    WallPost, SystemWallPost, MediaWallPost, TextWallPost, MediaWallPostPhoto,
    Reaction)

PROJECT_MODEL = get_project_model()
FUNDRAISER_MODEL = get_fundraiser_model()


class WallPostListSerializer(serializers.Field):
    """
    Serializer to serialize all wall-posts for an object into an array of ids
    Add a field like so:
    wallpost_ids = WallPostListSerializer()
    """
    def field_to_native(self, obj, field_name):
        content_type = ContentType.objects.get_for_model(obj)
        wallposts = WallPost.objects.filter(object_id=obj.id).filter(content_type=content_type)
        return wallposts.values_list('id', flat=True).order_by('-created').all()


class ReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for WallPost Reactions.
    """
    author = UserPreviewSerializer()
    text = ContentTextField()
    wallpost = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = Reaction
        fields = ('created', 'author', 'text', 'id', 'wallpost')


# Serializers for WallPosts.

class WallPostTypeField(serializers.Field):
    """ Used to add a type to WallPosts (e.g. media, text etc). """

    def __init__(self, type, **kwargs):
        super(WallPostTypeField, self).__init__(source='*', **kwargs)
        self.type = type

    def to_native(self, value):
        return self.type


class WallPostContentTypeField(serializers.SlugRelatedField):
    """
    Field to save content_type on wall-posts.
    """

    def from_native(self, data):
        if data == 'project':
            data = ContentType.objects.get_for_model(PROJECT_MODEL).model
        if data == 'fund raiser':
            data = ContentType.objects.get_for_model(FUNDRAISER_MODEL).model
        return super(WallPostContentTypeField, self).from_native(data)


class WallPostParentIdField(serializers.IntegerField):
    """
    Field to save object_id on wall-posts.
    """

    # Make an exception for project slugs.
    def from_native(self, value):
        if not value.isnumeric():
            # Assume a project slug here
            try:
                project = PROJECT_MODEL.objects.get(slug=value)
            except PROJECT_MODEL.DoesNotExist:
                raise ValidationError("No project with that slug")
            value = project.id
        return value


class WallPostSerializerBase(serializers.ModelSerializer):
    """
        Base class serializer for WallPosts. This is not used directly; please subclass it.
    """

    author = UserPreviewSerializer()
    reactions = ReactionSerializer(many=True, read_only=True)
    parent_type = WallPostContentTypeField(slug_field='model', source='content_type')
    parent_id = WallPostParentIdField(source='object_id')

    class Meta:
        fields = ('id', 'type', 'author', 'created', 'reactions', 'parent_type', 'parent_id', 'email_followers')


class MediaWallPostPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(required=False)
    mediawallpost = serializers.PrimaryKeyRelatedField(required=False, read_only=False)

    class Meta:
        model = MediaWallPostPhoto
        fields = ('id', 'photo', 'mediawallpost')


class MediaWallPostSerializer(WallPostSerializerBase):
    """
    Serializer for MediaWallPosts. This should not be used directly but instead should be subclassed for the specific
    model it's a WallPost about. See ProjectMediaWallPost for an example.
    """
    type = WallPostTypeField(type='media')
    text = ContentTextField(required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    photos = MediaWallPostPhotoSerializer(many=True, required=False)
    video_url = serializers.CharField(required=False)

    class Meta:
        model = MediaWallPost
        fields = WallPostSerializerBase.Meta.fields + ('text', 'video_html', 'video_url', 'photos')


class TextWallPostSerializer(WallPostSerializerBase):
    """
    Serializer for TextWallPosts. This should not be used directly but instead should be subclassed for the specific
    model it's a WallPost about. See ProjectTextWallPost for an example.
    """
    type = WallPostTypeField(type='text')
    text = ContentTextField()

    class Meta:
        model = TextWallPost
        fields = WallPostSerializerBase.Meta.fields + ('text',)


class WallPostRelatedField(serializers.RelatedField):
    def to_native(self, obj):
        return super(WallPostRelatedField, self).to_native(obj)


class SystemWallPostSerializer(WallPostSerializerBase):
    """
    Serializer for TextWallPosts. This should not be used directly but instead should be subclassed for the specific
    model it's a WallPost about. See ProjectTextWallPost for an example.
    """
    type = WallPostTypeField(type='system')
    text = ContentTextField()
    # related_type = serializers.CharField(source='related_type.model')
    # related_object = WallPostRelatedField(source='related_object')

    class Meta:
        model = TextWallPost
        fields = WallPostSerializerBase.Meta.fields + ('text', )


class WallPostSerializer(PolymorphicSerializer):

    class Meta:
        child_models = (
            (TextWallPost, TextWallPostSerializer),
            (MediaWallPost, MediaWallPostSerializer),
            (SystemWallPost, SystemWallPostSerializer),
        )
