from rest_framework import serializers
from django.core.urlresolvers import reverse
from wagtail.wagtailcore.blocks.field_block import RichTextBlock
from wagtail.wagtailimages.utils import generate_signature

from .models import Page


class BaseBlockSerializer(serializers.Serializer):

    def get_content(self, instance):
        return instance.block.get_prep_value(instance.value)

    def to_representation(self, instance):
        return {
            'content': self.get_content(instance),
            'block_type': instance.block_type
        }


class ImageBlockSerializer(BaseBlockSerializer):

    def get_content(self, instance):
        img = instance.value
        filter_spec = 'fill-800x300'
        signature = generate_signature(img.id, filter_spec)
        url = reverse('wagtailimages_serve', args=(signature, img.id, filter_spec))

        image_filename = img.file.name[len('original_images/'):]
        return  url + image_filename


class StreamSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        """
        Wallpost Polymorphic serialization
        """
        if obj.block_type == 'image':
           return ImageBlockSerializer(obj, context=self.context).to_representation(obj)
        return BaseBlockSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        model = RichTextBlock


class PageSerializer(serializers.ModelSerializer):
    body = StreamSerializer(many=True)

    class Meta:
        model = Page
        fields = ('title', 'id', 'slug', 'body')
