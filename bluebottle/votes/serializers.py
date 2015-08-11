from bluebottle.votes.models import Vote
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from rest_framework import serializers


class VoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    voter = UserPreviewSerializer(read_only=True)
    project = serializers.CharField(read_only=True)

    class Meta:
        model = Vote
        fields = ('id', 'voter', 'project')
