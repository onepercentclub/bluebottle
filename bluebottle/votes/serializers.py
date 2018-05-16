from rest_framework import serializers, exceptions

from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.votes.models import Vote
from bluebottle.projects.models import Project


class VoteSerializer(serializers.ModelSerializer):
    voter = UserPreviewSerializer(required=False, default=None)
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)

    def validate(self, data):
        data['voter'] = self.context['request'].user
        if Vote.has_voted(data['voter'], data['project']):
            raise exceptions.ValidationError('You already voted.')

        return data

    class Meta:
        model = Vote
        fields = ('id', 'voter', 'project', 'created')
