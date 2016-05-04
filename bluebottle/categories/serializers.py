from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from rest_framework import serializers

from bluebottle.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):

    id = serializers.CharField(source='slug', read_only=True)
    image = ImageSerializer(required=False)
    image_logo = ImageSerializer(required=False)
    description = serializers.CharField()
    title = serializers.CharField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'description', 'image', 'image_logo')
