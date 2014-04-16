from bluebottle.bluebottle_drf2.serializers import SorlImageField, OEmbedField
from rest_framework import serializers
from .models import Slide



class SlideSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField()
    image = SorlImageField('image', '800x600', crop='center')
    video = OEmbedField('video_url')

    class Meta:
        model = Slide
        #fields = ('title', 'contents', 'language', 'sequence')
