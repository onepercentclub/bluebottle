from builtins import object
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from rest_framework import serializers

from bluebottle.assignments.models import Assignment
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ContentTextField, PhotoSerializer)
from bluebottle.events.models import Event
from bluebottle.funding.models import Funding, Donation
from bluebottle.initiatives.models import Initiative
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.utils.serializers import MoneySerializer
from .models import Wallpost, SystemWallpost, MediaWallpost, TextWallpost, MediaWallpostPhoto, Reaction


class ReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallpost Reactions.
    """
    author = UserPreviewSerializer(read_only=True)
    text = ContentTextField()
    wallpost = serializers.PrimaryKeyRelatedField(queryset=Wallpost.objects)

    class Meta(object):
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
        if data == 'initiative':
            data = ContentType.objects.get_for_model(Initiative)
        elif data == 'event':
            data = ContentType.objects.get_for_model(Event)
        elif data == 'assignment':
            data = ContentType.objects.get_for_model(Assignment)
        elif data == 'funding':
            data = ContentType.objects.get_for_model(Funding)
        return data


class WallpostDonationSerializer(serializers.ModelSerializer):
    amount = MoneySerializer()
    user = UserPreviewSerializer()
    type = serializers.SerializerMethodField()

    class Meta(object):
        model = Donation
        fields = (
            'type',
            'id',
            'user',
            'amount',
            'name',
            'fundraiser',
            'reward',
            'anonymous',)

    def get_type(self, obj):
        return 'contributions/donations'

    def get_fields(self):
        """
        If the donation is anonymous, we do not return the user.
        """
        fields = super(WallpostDonationSerializer, self).get_fields()
        if isinstance(self.instance, Donation) and self.instance.anonymous:
            del fields['user']
        return fields


class WallpostSerializerBase(serializers.ModelSerializer):
    """
    Base class serializer for Wallposts. This is not used directly;
    please subclass it.
    """
    type = serializers.ReadOnlyField(source='wallpost_type', required=False)
    author = UserPreviewSerializer(read_only=True)
    parent_type = WallpostContentTypeField(slug_field='model',
                                           source='content_type')
    parent_id = serializers.IntegerField(source='object_id')
    reactions = ReactionSerializer(many=True, read_only=True, required=False)

    donation = serializers.PrimaryKeyRelatedField(queryset=Donation.objects, required=False, allow_null=True)

    def to_representation(self, instance):
        # We want to connect a donation by just sending the id,
        # but reading we want an embedded object, so we do a little trick here.
        response = super(WallpostSerializerBase, self).to_representation(instance)
        if instance.donation:
            response['donation'] = WallpostDonationSerializer(instance.donation, context=self.context).data
        return response

    class Meta(object):
        fields = ('id', 'type', 'author', 'created', 'reactions',
                  'parent_type', 'parent_id', 'pinned', 'donation',
                  'email_followers', 'share_with_facebook',
                  'share_with_twitter', 'share_with_linkedin')


class MediaWallpostPhotoSerializer(serializers.ModelSerializer):
    photo = PhotoSerializer(required=False)
    mediawallpost = serializers.PrimaryKeyRelatedField(required=False,
                                                       read_only=False,
                                                       queryset=MediaWallpost.objects)

    def validate(self, data):
        if 'mediawallpost' in data and data['mediawallpost'].author != self.instance.author:
            raise ValidationError('Wallpost author and photo author should match')

        return data

    class Meta(object):
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

    class Meta(object):
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

    class Meta(object):
        model = TextWallpost
        fields = WallpostSerializerBase.Meta.fields + ('text',)

    def validate(self, data):
        if (
            'donation' in data and
            TextWallpost.objects.filter(donation=data['donation'])
        ):
            raise ValidationError("Wallpost for donation already exists.")

        return super(WallpostSerializerBase, self).validate(data)


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

    class Meta(object):
        model = TextWallpost
        fields = WallpostSerializerBase.Meta.fields + ('text',)


class WallpostSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source='wallpost_type', required=False)
    author = UserPreviewSerializer()

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

    class Meta(object):
        model = Wallpost
        fields = ('id', 'type', 'author', 'created',
                  'email_followers', 'share_with_facebook',
                  'share_with_twitter', 'share_with_linkedin')
