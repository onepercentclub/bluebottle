from django.db.models import Q
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.assignments.models import Applicant
from bluebottle.assignments.transitions import ApplicantTransitions


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
                    ApplicantTransitions.values.new,
                    ApplicantTransitions.values.accepted,
                    ApplicantTransitions.values.active,
                    ApplicantTransitions.values.succeeded
                ])
            )
        else:
            queryset = queryset.instance_of(Applicant).filter(status__in=[
                ApplicantTransitions.values.new,
                ApplicantTransitions.values.accepted,
                ApplicantTransitions.values.active,
                ApplicantTransitions.values.succeeded
            ])
        return super(ApplicantListFilter, self).filter_queryset(request, queryset, view)
