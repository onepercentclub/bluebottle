import datetime

from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import transition, ModelTransitions
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions


class FundingTransitions(ActivityTransitions):
    def deadline_in_future(self):
        return not self.instance.deadline or self.instance.deadline > timezone.now()

    def is_complete(self):
        from bluebottle.funding.serializers import FundingSubmitSerializer
        serializer = FundingSubmitSerializer(
            data=model_to_dict(self.instance)
        )
        if not serializer.is_valid():
            print serializer.errors
            return _('Please make sure all required fields are filled in')

    def initiative_is_approved(self):
        if not self.instance.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @transition(
        source=ActivityTransitions.values.draft,
        target=ActivityTransitions.values.open,
        conditions=[is_complete, initiative_is_approved]
    )
    def open(self):
        pass

    @transition(
        source=ActivityTransitions.values.open,
        target=ActivityTransitions.values.running,
    )
    def start(self):
        if self.instance.duration:
            self.instance.deadline = timezone.now().date() + datetime.timedelta(days=self.instance.duration)

    @transition(
        source=ActivityTransitions.values.running,
        target=ActivityTransitions.values.done,
    )
    def done(self):
        pass

    @transition(
        source=ActivityTransitions.values.running,
        target=ActivityTransitions.values.closed,
    )
    def closed(self):
        pass

    @transition(
        source=[
            ActivityTransitions.values.done,
            ActivityTransitions.values.closed
        ],
        target=ActivityTransitions.values.running,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


class DonationTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        refunded = ChoiceItem('refunded', _('refunded'))

    def funding_is_running(self):
        return self.instance.activity.status == self.values.open

    @transition(
        source=[values.new, values.success],
        target=values.refunded,
    )
    def refund(self):
        pass

    @transition(
        source=[values.new, values.success],
        target=values.failed,
    )
    def fail(self):
        pass

    @transition(
        source=[values.new, values.failed],
        target=values.success,
    )
    def succeed(self):
        pass


class PaymentTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        success = ChoiceItem('success', _('success'))
        refunded = ChoiceItem('refunded', _('refunded'))
        refund_requested = ChoiceItem('refund_requested', _('refund requested'))
        failed = ChoiceItem('failed', _('failed'))

    @transition(
        source=[values.new],
        target=values.success
    )
    def succeed(self):
        self.instance.donation.transitions.succeed()
        self.instance.donation.save()

    @transition(
        source=[values.new, values.success],
        target='failed'
    )
    def fail(self):
        self.instance.donation.transitions.fail()
        self.instance.donation.save()

    @transition(
        source=[values.success],
        target=values.refunded
    )
    def refund(self):
        self.instance.donation.transitions.refund()
        self.instance.donation.save()
