from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.deeds.models import DeedParticipant
from bluebottle.deeds.states import DeedParticipantStateMachine


class ParticipantListFilter(DjangoFilterBackend):
    """
    Filter that shows all participants if user is owner,
    otherwise only show accepted participants.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.instance_of(DeedParticipant).filter(
                Q(user=request.user) |
                Q(activity__owner=request.user) |
                Q(activity__initiative__activity_managers=request.user) |
                Q(status__in=[
                    DeedParticipantStateMachine.accepted.value,
                    DeedParticipantStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.instance_of(
                DeedParticipant
            ).filter(
                status__in=[
                    DeedParticipantStateMachine.accepted.value,
                    DeedParticipantStateMachine.succeeded.value
                ])
        return super().filter_queryset(request, queryset, view)
