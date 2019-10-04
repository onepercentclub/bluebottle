from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from rest_framework import serializers

from bluebottle.categories.models import Category, CategoryContent


class CategoryContentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=False)
    image = ImageSerializer(required=False)
    video_url = serializers.URLField(required=False)
    link_text = serializers.CharField(required=True)
    link_url = serializers.URLField(required=True)
    sequence = serializers.IntegerField(read_only=True)

    class Meta:
        model = CategoryContent
        fields = ('title', 'description', 'image', 'video_url', 'link_text', 'link_url', 'sequence')


class CategorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    title = serializers.CharField()
    description = serializers.CharField()
    image = ImageSerializer(required=False)
    image_logo = ImageSerializer(required=False)
    contents = CategoryContentSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'title', 'description', 'image', 'image_logo', 'contents')
