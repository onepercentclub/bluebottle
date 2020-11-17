from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.time_based.models import PeriodParticipant, DateParticipant
from bluebottle.time_based.states import ApplicationStateMachine


class ApplicationListFilter(DjangoFilterBackend):
    """
    Filter that shows all applicant if user is owner,
    otherwise only show accepted applicants.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.instance_of(DateParticipant, PeriodParticipant).filter(
                Q(user=request.user) |
                Q(activity__owner=request.user) |
                Q(activity__initiative__activity_manager=request.user) |
                Q(status__in=[
                    ApplicationStateMachine.new.value,
                    ApplicationStateMachine.accepted.value,
                    ApplicationStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.instance_of(
                PeriodParticipant, DateParticipant
            ).filter(
                status__in=[
                    ApplicationStateMachine.new.value,
                    ApplicationStateMachine.accepted.value,
                    ApplicationStateMachine.succeeded.value
                ])
        return super().filter_queryset(request, queryset, view)
