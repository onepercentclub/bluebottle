from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.assignments.models import Applicant
from bluebottle.assignments.states import ApplicantStateMachine


class ApplicantListFilter(DjangoFilterBackend):
    """
    Filter that shows all applicant if user is owner,
    otherwise only show accepted applicants.
    """
    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated():
            queryset = queryset.instance_of(Applicant).filter(
                Q(user=request.user) |
                Q(activity__owner=request.user) |
                Q(activity__initiative__activity_manager=request.user) |
                Q(status__in=[
                    ApplicantStateMachine.new.value,
                    ApplicantStateMachine.accepted.value,
                    ApplicantStateMachine.active.value,
                    ApplicantStateMachine.succeeded.value
                ])
            )
        else:
            queryset = queryset.instance_of(Applicant).filter(status__in=[
                ApplicantStateMachine.new.value,
                ApplicantStateMachine.accepted.value,
                ApplicantStateMachine.active.value,
                ApplicantStateMachine.succeeded.value
            ])
        return super().filter_queryset(request, queryset, view)
