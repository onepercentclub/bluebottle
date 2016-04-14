from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.projects.models import PartnerOrganization
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):

    image = ImageSerializer(required=False)
    description = serializers.CharField()
    title = serializers.CharField()

    class Meta:
        model = PartnerOrganization
        fields = ('id', 'title', 'description', 'image')
