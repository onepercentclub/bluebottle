from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
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


class DonationAdminStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = DonationTransitions.values.succeeded

    def lookups(self, request, model_admin):
        return DonationTransitions.values.choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_status,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(status=self.default_status)
        if self.value() != 'all':
            return queryset.filter(status=self.value())
        return queryset
