from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import transition, ModelTransitions
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions


class FundingTransitions(ActivityTransitions):
    serializer = 'bluebottle.events.serializers.EventSubmitSerializer'

    class values(ActivityTransitions.values):
        partially_funded = ChoiceItem('partially_funded', _('partially funded'))
        refunded = ChoiceItem('refunded', _('refunded'))

    def deadline_in_future(self):
        return not self.instance.deadline or self.instance.deadline > timezone.now()

    @transition(
        source=values.open,
        target=values.partially_funded,
    )
    def partial(self):
        pass

    @transition(
        source=values.open,
        target=values.succeeded,
    )
    def succeed(self):
        pass

    @transition(
        source=values.partially_funded,
        target=values.succeeded,
    )
    def approve(self):
        pass

    @transition(
        source=values.partially_funded,
        target=values.refunded,
    )
    def refund(self):
        pass

    @transition(
        source='*',
        target=values.closed,
    )
    def closed(self):
        pass

    @transition(
        source=[
            values.partially_funded, values.closed, values.succeeded
        ],
        target=values.open,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


class DonationTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        refunded = ChoiceItem('refunded', _('refunded'))

    def funding_is_open(self):
        return self.instance.activity.status == self.values.open

    @transition(
        source=[values.new, values.succeeded],
        target=values.refunded,
    )
    def refund(self):
        pass

    @transition(
        source=[values.new, values.succeeded],
        target=values.failed,
    )
    def fail(self):
        pass

    @transition(
        source=[values.new, values.failed],
        target=values.succeeded,
    )
    def succeed(self):
        pass


class PaymentTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        refunded = ChoiceItem('refunded', _('refunded'))
        refund_requested = ChoiceItem('refund_requested', _('refund requested'))
        failed = ChoiceItem('failed', _('failed'))

    @transition(
        source=[values.new],
        target=values.succeeded
    )
    def succeed(self):
        self.instance.donation.transitions.succeed()
        self.instance.donation.save()

    @transition(
        source=[values.new, values.succeeded],
        target='failed'
    )
    def fail(self):
        self.instance.donation.transitions.fail()
        self.instance.donation.save()

    @transition(
        source=[values.succeeded],
        target=values.refunded
    )
    def refund(self):
        self.instance.donation.transitions.refund()
        self.instance.donation.save()
