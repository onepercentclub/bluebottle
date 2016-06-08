from rest_framework import serializers
from wagtail.wagtailcore.blocks.field_block import RichTextBlock, CharBlock

from .models import Page

class BaseBlockSerializer(serializers.Serializer):

    def to_representation(self, instance):
        return {
            'content': instance.block.get_prep_value(instance.value),
            'block_type': instance.block_type
        }

class PolymorphicBlockSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        """
        Wallpost Polymorphic serialization
        """
        if obj.block_type == 'heading':
           return BaseBlockSerializer(obj, context=self.context).to_representation(obj)
        return BaseBlockSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        model = RichTextBlock


class PageSerializer(serializers.ModelSerializer):
    body = PolymorphicBlockSerializer(many=True)

    class Meta:
        model = Page
        fields = ('title', 'id', 'slug', 'body')
