from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ContentTextField, PhotoSerializer)
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.projects.models import Project

from .models import Wallpost, SystemWallpost, MediaWallpost, TextWallpost, MediaWallpostPhoto, Reaction


class ReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallpost Reactions.
    """
    author = UserPreviewSerializer()
    text = ContentTextField()
    wallpost = serializers.PrimaryKeyRelatedField(queryset=Wallpost.objects)

    class Meta:
        model = Reaction
        fields = ('created', 'author', 'text', 'id', 'wallpost')


# Serializers for Wallposts.

class WallpostContentTypeField(serializers.SlugRelatedField):
    """
    Field to save content_type on wall-posts.
    """

    def get_queryset(self):
        return ContentType.objects

    def to_internal_value(self, data):
        if data == 'project':
            data = ContentType.objects.get_for_model(Project).model
        if data == 'fundraiser':
            data = ContentType.objects.get_for_model(Fundraiser).model
        return super(WallpostContentTypeField, self).to_internal_value(data)


class WallpostParentIdField(serializers.IntegerField):
    """
    Field to save object_id on wall-posts.
    """

    # Make an exception for project slugs.
    def to_internal_value(self, value):
        if not value.isnumeric():
            # Assume a project slug here
            try:
                project = Project.objects.get(slug=value)
            except Project.DoesNotExist:
                raise ValidationError("No project with that slug")
            value = project.id
        return value


class WallpostSerializerBase(serializers.ModelSerializer):
    """
    Base class serializer for Wallposts. This is not used directly;
    please subclass it.
    """
    type = serializers.ReadOnlyField(source='wallpost_type', required=False)
    author = UserPreviewSerializer()
    parent_type = WallpostContentTypeField(slug_field='model',
                                           source='content_type')
    parent_id = WallpostParentIdField(source='object_id')
    reactions = ReactionSerializer(many=True, read_only=True, required=False)

    class Meta:
        fields = ('id', 'type', 'author', 'created', 'reactions',
                  'parent_type', 'parent_id', 'pinned', 'donation',
                  'email_followers', 'share_with_facebook',
                  'share_with_twitter', 'share_with_linkedin')


class MediaWallpostPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(required=False)
    mediawallpost = serializers.PrimaryKeyRelatedField(required=False,
                                                       read_only=False,
                                                       queryset=MediaWallpost.objects)

    class Meta:
        model = MediaWallpostPhoto
        fields = ('id', 'photo', 'mediawallpost')


class MediaWallpostSerializer(WallpostSerializerBase):
    """
    Serializer for MediaWallposts. This should not be used directly but instead
    should be subclassed for the specific
    model it's a Wallpost about. See ProjectMediaWallpost for an example.
    """
    text = ContentTextField(required=False)
    video_html = OEmbedField(source='video_url',
                             maxwidth='560',
                             maxheight='315')
    photos = MediaWallpostPhotoSerializer(many=True, required=False)
    video_url = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = MediaWallpost
        fields = WallpostSerializerBase.Meta.fields + ('text', 'video_html',
                                                       'video_url', 'photos')


class TextWallpostSerializer(WallpostSerializerBase):
    """
    Serializer for TextWallposts. This should not be used directly but instead
    should be subclassed for the specific
    model it's a Wallpost about. See ProjectTextWallpost for an example.
    """
    text = ContentTextField()

    class Meta:
        model = TextWallpost
        fields = WallpostSerializerBase.Meta.fields + ('text',)


class WallpostRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return super(WallpostRelatedField, self).to_representation(obj)


class SystemWallpostSerializer(WallpostSerializerBase):
    """
    Serializer for TextWallposts. This should not be used directly but instead
    should be subclassed for the specific
    model it's a Wallpost about. See ProjectTextWallpost for an example.
    """
    text = ContentTextField()

    # related_type = serializers.CharField(source='related_type.model')
    # related_object = WallpostRelatedField(source='related_object')

    class Meta:
        model = TextWallpost
        fields = WallpostSerializerBase.Meta.fields + ('text',)


class WallpostSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source='wallpost_type', required=False)

    def to_representation(self, obj):
        """
        Wallpost Polymorphic serialization
        """
        if isinstance(obj, TextWallpost):
            return TextWallpostSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, MediaWallpost):
            return MediaWallpostSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, SystemWallpost):
            return SystemWallpostSerializer(obj, context=self.context).to_representation(obj)
        return super(WallpostSerializer, self).to_representation(obj)

    class Meta:
        model = Wallpost
        fields = ('id', 'type', 'author', 'created',
                  'email_followers', 'share_with_facebook',
                  'share_with_twitter', 'share_with_linkedin')
