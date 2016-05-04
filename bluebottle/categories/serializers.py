from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from rest_framework import serializers

from bluebottle.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):

    image = ImageSerializer(required=False)
    image_logo = ImageSerializer(required=False)
    description = serializers.CharField()
    title = serializers.CharField()
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'slug', 'title', 'description', 'image', 'image_logo')
