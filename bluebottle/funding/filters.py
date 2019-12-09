from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from rest_framework_json_api.django_filters import DjangoFilterBackend

from bluebottle.funding.models import PaymentProvider
from bluebottle.funding.transitions import DonationTransitions
from bluebottle.funding_pledge.models import PledgePayment


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
        return (('all', _('All')), ) + DonationTransitions.values.choices

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
        if self.value() == 'all':
            return queryset
        return queryset.filter(status=self.value())


class DonationAdminCurrencyFilter(SimpleListFilter):
    title = _('Currency')

    parameter_name = 'amount_currency__exact'

    def lookups(self, request, model_admin):
        return [('all', _('All')), ] + PaymentProvider.get_currency_choices()

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() and self.value() != 'all':
            return queryset.filter(amount_currency=self.value())
        return queryset


class DonationAdminPledgeFilter(SimpleListFilter):
    title = _('Pledged')

    parameter_name = 'pledge'
    default_status = DonationTransitions.values.succeeded

    def lookups(self, request, model_admin):
        return (
            ('all', _('Any')),
            ('pledged', _('Pledged donations')),
            ('paid', _('Paid donations')),
        )

    def queryset(self, request, queryset):
        pledge_ctype = ContentType.objects.get_for_model(PledgePayment)
        if self.value() == 'paid':
            return queryset.exclude(payment__polymorphic_ctype=pledge_ctype)
        elif self.value() == 'pledged':
            return queryset.filter(payment__polymorphic_ctype=pledge_ctype)
        return queryset
