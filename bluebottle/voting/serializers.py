from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user
from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField, SerializerMethodResourceRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.utils.fields import RichTextField
from bluebottle.voting.models import Poll, PollOption, PollVote


class PollOptionSerializer(ModelSerializer):
    title = serializers.CharField()
    description = RichTextField(required=False, allow_blank=True)
    image = ImageSerializer(required=False, allow_null=True)
    video_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sequence = serializers.IntegerField(read_only=True)
    votes = serializers.IntegerField(read_only=True, source='vote_count', allow_null=True)
    percentage = serializers.IntegerField(read_only=True, allow_null=True)
    winner = serializers.BooleanField(read_only=True, allow_null=True)

    def get_fields(self):
        fields = super().get_fields()
        poll = getattr(self.instance, 'poll', None)
        if poll is not None and poll.status != 'closed':
            del fields['votes']
            del fields['percentage']
            del fields['winner']
        return fields

    class Meta:
        model = PollOption
        fields = (
            'id', 'title', 'description', 'image', 'video_url', 'sequence',
            'votes', 'percentage', 'winner',
        )

    class JSONAPIMeta:
        resource_name = 'polls/options'


class PollVoteSerializer(ModelSerializer):
    poll = ResourceRelatedField(queryset=Poll.objects.all())
    option = ResourceRelatedField(queryset=PollOption.objects.all())

    class Meta:
        model = PollVote
        fields = (
            'id', 'poll', 'option'
        )

    class JSONAPIMeta:
        resource_name = 'polls/votes'
        included_resources = ['option']

    included_serializers = {
        'option': 'bluebottle.voting.serializers.PollOptionSerializer',
        'poll': 'bluebottle.voting.serializers.PollSerializer',
    }

    def validate(self, data):
        if self.instance:
            data.pop('poll', None)
            poll = self.instance.poll
            option = data.get('option', self.instance.option)
        else:
            option = data.get('option')
            poll = data.get('poll')
            if option and not poll:
                poll = option.poll
                data['poll'] = poll

        if option and poll and option.poll_id != poll.id:
            raise serializers.ValidationError({
                'option': _('This option does not belong to this poll')
            })

        if poll and poll.status != 'open':
            raise serializers.ValidationError(
                _('This poll is not open for voting')
            )

        return data


class PollSerializer(ModelSerializer):
    title = serializers.CharField()
    subtitle = serializers.CharField(required=False, allow_blank=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    options = ResourceRelatedField(many=True, read_only=True)
    votes_cast = serializers.IntegerField(read_only=True)
    my_vote = SerializerMethodResourceRelatedField(
        model=PollVote,
        many=False,
        read_only=True,
    )

    class Meta:
        model = Poll
        fields = (
            'id', 'title', 'subtitle', 'end_date', 'status', 'options',
            'votes_cast', 'my_vote',
        )

    class JSONAPIMeta:
        resource_name = 'polls'
        included_resources = ['options', 'my_vote']

    included_serializers = {
        'options': 'bluebottle.voting.serializers.PollOptionSerializer',
        'my_vote': 'bluebottle.voting.serializers.PollVoteSerializer',
    }

    def get_my_vote(self, obj):
        user = get_current_user()
        if user and user.is_authenticated:
            return obj.votes.filter(owner=user).first()
        return None
