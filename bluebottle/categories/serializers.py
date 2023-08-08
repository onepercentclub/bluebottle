from builtins import object

from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.categories.models import Category, CategoryContent


class CategoryContentSerializer(ModelSerializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=False)
    image = ImageSerializer(required=False)
    link_text = serializers.CharField(required=False)
    link_url = serializers.URLField(required=False)
    sequence = serializers.IntegerField(read_only=True)

    class Meta(object):
        model = CategoryContent
        fields = ('title', 'description', 'image', 'link_text', 'link_url', 'sequence')

    class JSONAPIMeta(object):
        resource_name = 'category/content'


class CategorySerializer(ModelSerializer):
    title = serializers.CharField()
    description = serializers.CharField()
    image = ImageSerializer(required=False)
    image_logo = ImageSerializer(required=False)
    contents = CategoryContentSerializer(many=True, read_only=True)

    class Meta(object):
        model = Category
        fields = ('id', 'slug', 'title', 'description', 'image', 'image_logo', 'contents')

    class JSONAPIMeta(object):
        resource_name = 'categories'
