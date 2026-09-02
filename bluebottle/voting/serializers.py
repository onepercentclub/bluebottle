from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField, SerializerMethodResourceRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from django.utils.translation import gettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.utils.utils import clean_html
from bluebottle.voting.models import Poll, PollOption, PollVote


class PollOptionSerializer(ModelSerializer):
    title = serializers.CharField()
    description = serializers.SerializerMethodField()
    image = ImageSerializer(required=False, allow_null=True)
    video_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sequence = serializers.IntegerField(read_only=True)

    class Meta:
        model = PollOption
        fields = (
            'id', 'title', 'description', 'image', 'video_url', 'sequence'
        )

    class JSONAPIMeta:
        resource_name = 'polls/options'

    def get_description(self, obj):
        value = obj.description
        if not value:
            return ''
        html = getattr(value, 'html', None)
        if not html:
            return ''
        return clean_html(html)


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
    votes_cast = serializers.SerializerMethodField()
    my_vote = SerializerMethodResourceRelatedField(
        model=PollVote,
        many=False,
        read_only=True,
        source='get_my_vote',
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

    def get_votes_cast(self, obj):
        votes_cast = getattr(obj, 'votes_cast', None)
        if isinstance(votes_cast, int):
            return votes_cast
        return obj.votes.count()

    def get_my_vote(self, obj):
        if hasattr(obj, 'user_votes'):
            return obj.user_votes[0] if obj.user_votes else None

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        return obj.votes.filter(owner=user).first()
