from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from bluebottle.funding.models import PaymentProvider
from bluebottle.funding.states import DonorStateMachine
from bluebottle.funding_pledge.models import PledgePayment


class DonorAdminStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = DonorStateMachine.succeeded.value

    def lookups(self, request, model_admin):
        return [('all', _('All'))] + [
            (s.value, s.name.title()) for s in list(DonorStateMachine.states.values())
        ]

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


class DonorAdminCurrencyFilter(SimpleListFilter):
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


class DonorAdminPledgeFilter(SimpleListFilter):
    title = _('Pledged')

    parameter_name = 'pledge'
    default_status = DonorStateMachine.succeeded.value

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
