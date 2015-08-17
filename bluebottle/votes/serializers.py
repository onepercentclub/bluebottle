from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.votes.models import Vote
from rest_framework import serializers


class VoteSerializer(serializers.ModelSerializer):
    voter = get_serializer_class('AUTH_USER_MODEL', 'preview')(read_only=True)
    project = serializers.SlugRelatedField(source='project', slug_field='slug')

    class Meta:
        model = Vote
        fields = ('id', 'voter', 'project', 'created')
