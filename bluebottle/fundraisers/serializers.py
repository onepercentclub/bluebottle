from django.utils.translation import ugettext as _
from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import ImageSerializer, OEmbedField, SorlImageField
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.members.serializers import UserProfileSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer


class BaseFundraiserSerializer(serializers.ModelSerializer):
    """ Serializer to view/create fundraisers """

    owner = UserProfileSerializer(read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    image = ImageSerializer()
    video_html = OEmbedField(source='video_url', maxwidth='560',
                             maxheight='315')

    amount = MoneySerializer()
    amount_donated = MoneySerializer()

    class Meta:
        model = Fundraiser
        fields = ('id', 'owner', 'project', 'title', 'description', 'image',
                  'created', 'video_html', 'video_url', 'amount',
                  'amount_donated', 'deadline')

    def validate(self, data):
        if not data['deadline'] or data['deadline'] > data['project'].deadline:
            raise serializers.ValidationError(
                {'deadline': [_("Fundraiser deadline exceeds project deadline.")]}
            )
        return data
