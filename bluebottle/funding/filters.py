from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.funding.transitions import DonationTransitions


class DonationListFilter(DjangoFilterBackend):
    """
    Filter that shows only successful contributions
    """
    def filter_queryset(self, request, queryset, view):
        queryset = queryset.filter(status__in=[
            DonationTransitions.values.succeeded
        ])

        return super(DonationListFilter, self).filter_queryset(request, queryset, view)
