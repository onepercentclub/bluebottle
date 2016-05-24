from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.votes.models import Vote
from rest_framework import serializers


class VoteSerializer(serializers.ModelSerializer):
    voter = UserPreviewSerializer(read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Vote.objects)

    class Meta:
        model = Vote
        fields = ('id', 'voter', 'project', 'created')
