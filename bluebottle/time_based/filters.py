from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.time_based.models import PeriodParticipant, DateParticipant
from bluebottle.time_based.states import ParticipantStateMachine, SlotParticipantStateMachine


class ParticipantListFilter(DjangoFilterBackend):
    """
    Filter that shows all participants if user is owner,
    otherwise only show accepted participants.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.instance_of(DateParticipant, PeriodParticipant).filter(
                Q(user=request.user) |
                Q(activity__owner=request.user) |
                Q(activity__initiative__activity_manager=request.user) |
                Q(status__in=[
                    ParticipantStateMachine.new.value,
                    ParticipantStateMachine.accepted.value,
                    ParticipantStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.instance_of(
                PeriodParticipant, DateParticipant
            ).filter(
                status__in=[
                    ParticipantStateMachine.new.value,
                    ParticipantStateMachine.accepted.value,
                    ParticipantStateMachine.succeeded.value
                ])
        return super().filter_queryset(request, queryset, view)


class SlotParticipantListFilter(DjangoFilterBackend):
    """
    Filter that shows all slot participants if user is owner,
    otherwise only show accepted participants.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.filter(
                Q(participant__user=request.user) |
                Q(participant__activity__owner=request.user) |
                Q(participant__activity__initiative__activity_manager=request.user) |
                Q(status=SlotParticipantStateMachine.registered.value)
            ).filter(
                Q(participant__user=request.user) |
                Q(participant__status__in=[
                    ParticipantStateMachine.new.value,
                    ParticipantStateMachine.accepted.value,
                    ParticipantStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.filter(
                status=SlotParticipantStateMachine.registered.value
            ).filter(
                participant__status__in=[
                    ParticipantStateMachine.new.value,
                    ParticipantStateMachine.accepted.value,
                    ParticipantStateMachine.succeeded.value
                ]
            )
        return queryset
