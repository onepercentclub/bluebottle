from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.events.models import Participant
from bluebottle.events.states import ParticipantStateMachine


class ParticipantListFilter(DjangoFilterBackend):
    """
    Filter that shows all participants if user is owner,
    otherwise only show accepted participants.
    """
    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.filter(
                Q(user=request.user) |
                Q(activity__owner=request.user) |
                Q(status__in=[
                    ParticipantStateMachine.new.value,
                    ParticipantStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.filter(status__in=[
                ParticipantStateMachine.new.value,
                ParticipantStateMachine.succeeded.value
            ])

        queryset = queryset.instance_of(Participant)

        return super().filter_queryset(request, queryset, view)
