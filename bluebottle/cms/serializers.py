import json

from bluebottle.projects.models import Project
from bluebottle.projects.serializers import ProjectPreviewSerializer
from rest_framework import serializers
from django.core.urlresolvers import reverse
from wagtail.wagtailcore.blocks.field_block import RichTextBlock
from wagtail.wagtailimages.utils import generate_signature

from .models import Page

def get_image_url(image, filter_spec='fill-800x300'):
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    image_filename = image.file.name[len('original_images/'):]
    return  url + image_filename


class BaseBlockSerializer(serializers.Serializer):

    def get_content(self, instance):
        return instance.block.get_prep_value(instance.value)

    def get_elements(self, instance):
        return []

    def to_representation(self, instance):
        return {
            'id': instance.__hash__(),
            'content': self.get_content(instance),
            'items': self.get_elements(instance),
            'block_type': instance.block_type
        }


class ImageBlockSerializer(BaseBlockSerializer):

    def get_content(self, instance):
        img = instance.value
        filter_spec = 'fill-800x300'
        signature = generate_signature(img.id, filter_spec)
        url = reverse('wagtailimages_serve', args=(signature, img.id, filter_spec))

        image_filename = img.file.name[len('original_images/'):]
        return  url


class ArticleSerializer(BaseBlockSerializer):

    def get_content(self, instance):
        return None

    def get_elements(self, instance):
        return {
            'title': instance.value['title'],
            'text': instance.value['text'].source,
            'image': get_image_url(instance.value['image'], 'fill-800x400')
        }


class StepBlockSerializer(BaseBlockSerializer):

    def get_blocks(self, blocks):
        serialized = []
        for block in blocks:
            serialized += [
                {
                    'title': block['title'],
                    'text': block['text'],
                    'image': get_image_url(block['image'], 'fill-300x300')
                }
            ]
        return serialized

    def get_content(self, instance):
        return None

    def get_elements(self, instance):
        return {
            'blocks': self.get_blocks(instance.value),
        }


class BlockItemSectionSerializer(BaseBlockSerializer):

    def get_blocks(self, blocks):
        serialized = []
        for block in blocks:
            serialized += [
                {
                    'title': block['title'],
                    'text': block['text'],
                    'image': get_image_url(block['image'], 'fill-300x300')
                }
            ]
        return serialized

    def get_content(self, instance):
        return None

    def get_elements(self, instance):
        return {
            'title': instance.value['title'],
            'intro': instance.value['intro'],
            'blocks': self.get_blocks(instance.value['blocks']),
            'button': instance.value['button'],
        }


class ProjectSectionSerializer(BaseBlockSerializer):

    def get_content(self, instance):
        return None

    def get_elements(self, instance):
        return {
            'title': instance.value['title'],
            'projects': ProjectPreviewSerializer(many=True).to_representation(instance.value['projects']),
        }


class StreamSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        """
        Wallpost Polymorphic serialization
        """
        if obj.block_type == 'image':
           return ImageBlockSerializer(obj, context=self.context).to_representation(obj)
        if obj.block_type == 'step_blocks':
           return StepBlockSerializer(obj, context=self.context).to_representation(obj)
        if obj.block_type == 'article':
           return ArticleSerializer(obj, context=self.context).to_representation(obj)
        if obj.block_type == 'block_items':
           return BlockItemSectionSerializer(obj, context=self.context).to_representation(obj)
        if obj.block_type == 'projects':
           return ProjectSectionSerializer(obj, context=self.context).to_representation(obj)
        return BaseBlockSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        model = RichTextBlock


class PageSerializer(serializers.ModelSerializer):
    body = StreamSerializer(many=True)

    class Meta:
        model = Page
        fields = ('title', 'id', 'slug', 'body')
