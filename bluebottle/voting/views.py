from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from bluebottle.utils.permissions import OneOf, ResourceOwnerPermission, ResourcePermission
from bluebottle.utils.views import (
    CreateAPIView, JsonApiViewMixin, RetrieveAPIView, RetrieveUpdateDestroyAPIView
)
from bluebottle.voting.models import Poll, PollVote
from bluebottle.voting.serializers import PollSerializer, PollVoteSerializer


class PollDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = Poll.objects.filter(status__in=['open', 'closed'])
    serializer_class = PollSerializer


class PollVoteList(JsonApiViewMixin, CreateAPIView):
    queryset = PollVote.objects.all()
    serializer_class = PollVoteSerializer
    permission_classes = (
        IsAuthenticated,
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def perform_create(self, serializer):
        serializer.validated_data['owner'] = self.request.user
        try:
            with transaction.atomic():
                super().perform_create(serializer)
        except IntegrityError:
            raise ValidationError(
                _('You have already voted in this poll')
            )


class PollVoteDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = PollVote.objects.all()
    serializer_class = PollVoteSerializer
    permission_classes = (
        IsAuthenticated,
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def perform_destroy(self, instance):
        if instance.poll.status != 'open':
            raise ValidationError(_('This poll is not open for voting'))
        super().perform_destroy(instance)
