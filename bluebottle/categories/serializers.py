from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from rest_framework import serializers

from bluebottle.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):

    image = ImageSerializer(required=False)
    description = serializers.CharField()
    title = serializers.CharField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'description', 'image')
