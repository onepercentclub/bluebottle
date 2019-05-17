import datetime

from django.db import models
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem
from moneyed.classes import Money
from multiselectfield import MultiSelectField

from bluebottle.activities.models import Activity, Contribution
from bluebottle.notifications.decorators import transition
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField, get_currency_choices


class Funding(Activity):
    deadline = models.DateField(_('deadline'), null=True, blank=True)
    duration = models.PositiveIntegerField(_('duration'), null=True, blank=True)

    target = MoneyField()
    accepted_currencies = MultiSelectField(
        max_length=100, default=[],
        choices=lazy(get_currency_choices, tuple)()
    )

    class Meta:
        verbose_name = _("Funding")
        verbose_name_plural = _("Funding Activities")
        permissions = (
            ('api_read_funding', 'Can view funding through the API'),
            ('api_add_funding', 'Can add funding through the API'),
            ('api_change_funding', 'Can change funding through the API'),
            ('api_delete_funding', 'Can delete funding through the API'),

            ('api_read_own_funding', 'Can view own funding through the API'),
            ('api_add_own_funding', 'Can add own funding through the API'),
            ('api_change_own_funding', 'Can change own funding through the API'),
            ('api_delete_own_funding', 'Can delete own funding through the API'),
        )

    @property
    def amount_raised(self):
        """
        The sum of all contributions (donations) converted to the targets currency
        """
        totals = self.contributions.filter(
            status='success'
        ).values(
            'donation__amount_currency'
        ).annotate(
            total=Sum('donation__amount')
        )
        amounts = [Money(total['total'], total['donation__amount_currency']) for total in totals]
        amounts = [convert(amount, self.target.currency) for amount in amounts]

        return sum(amounts) or Money(0, self.target.currency)

    def deadline_in_future(self):
        return not self.deadline or self.deadline > timezone.now()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.running,
    )
    def start(self):
        if self.duration:
            self.deadline = timezone.now().date() + datetime.timedelta(days=self.duration)

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
    )
    def done(self):
        pass

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.closed,
    )
    def closed(self):
        pass

    @transition(
        field='status',
        source=[Activity.Status.done, Activity.Status.closed],
        target=Activity.Status.running,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


class Donation(Contribution):
    class Status(Contribution.Status):
        refunded = ChoiceItem('refunded', _('refunded'))

    amount = MoneyField()

    def funding_is_running(self):
        return self.activity.status == Activity.Status.open

    @transition(
        field='status',
        source=[Status.new, Status.success],
        target=Status.refunded,
        conditions=[funding_is_running]
    )
    def refund(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[Status.new, Status.success],
        target=Status.failed,
        conditions=[funding_is_running]
    )
    def fail(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[Status.new, Status.failed],
        target=Status.success,
        conditions=[funding_is_running]
    )
    def success(self, **kwargs):
        pass
