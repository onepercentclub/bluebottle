from builtins import object
from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer
)
from bluebottle.projects.models import ProjectImage


class ProjectImageSerializer(serializers.ModelSerializer):
    """
    Members that wrote a wallpost
    """
    image = ImageSerializer(source='file')

    class Meta(object):
        model = ProjectImage
        fields = ('id', 'image')
