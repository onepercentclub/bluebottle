from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from bluebottle.utils.permissions import OneOf, ResourceOwnerPermission, ResourcePermission
from bluebottle.utils.views import (
    CreateAPIView, ExportView, JsonApiViewMixin, RetrieveAPIView,
    RetrieveUpdateDestroyAPIView
)
from bluebottle.voting.models import Poll, PollVote
from bluebottle.voting.serializers import PollSerializer, PollVoteSerializer


class PollDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = Poll.objects.filter(status__in=['open', 'closed'])
    serializer_class = PollSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            'options'
        ).annotate(votes_cast=Count('votes'))

        user = self.request.user
        if user and user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PollVote.objects.filter(owner=user),
                    to_attr='user_votes',
                )
            )

        return queryset


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


class PollVoteExportView(ExportView):
    fields = (
        ('owner__full_name', 'Name'),
        ('owner__email', 'Email'),
        ('created', 'Date'),
        ('option__title', 'Option'),
    )

    model = Poll
    filename = 'votes'

    def get_instances(self):
        return self.get_object().votes.select_related('owner', 'option').all()
