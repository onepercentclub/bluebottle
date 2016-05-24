from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.votes.models import Vote
from bluebottle.projects.models import Project
from rest_framework import serializers


class VoteSerializer(serializers.ModelSerializer):
    voter = UserPreviewSerializer(required=False, default=None)
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)

    class Meta:
        model = Vote
        fields = ('id', 'voter', 'project', 'created')
