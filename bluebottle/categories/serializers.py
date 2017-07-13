from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from rest_framework import serializers

from bluebottle.categories.models import Category, CategoryContent


class CategoryContentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = ImageSerializer(required=False)
    video_url = serializers.URLField(required=False)
    link = serializers.URLField(required=False)

    class Meta:
        model = CategoryContent
        fields = ('title', 'description', 'image', 'video_url', 'link')


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
