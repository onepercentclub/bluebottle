from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem
from stripe.error import StripeError

from bluebottle.fsm import transition, TransitionNotPossible
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.transitions import PaymentTransitions, PayoutAccountTransitions
from bluebottle.funding_stripe.utils import stripe


class StripePaymentTransitions(PaymentTransitions):
    @transition(
        source=[PaymentTransitions.values.succeeded],
        target=PaymentTransitions.values.refund_requested
    )
    def request_refund(self):
        intent = stripe.PaymentIntent.retrieve(self.instance.intent_id)

        intent.charges[0].refund(
            reverse_transfer=True,
        )


class StripeSourcePaymentTransitions(PaymentTransitions):
    class values(PaymentTransitions.values):
        charged = ChoiceItem('charged', _('charged'))
        canceled = ChoiceItem('canceled', _('canceled'))
        disputed = ChoiceItem('disputed', _('disputed'))

    def has_charge_token(self):
        if not self.instance.charge_token:
            return _('Missing charge token')

    @transition(
        source=[values.charged],
        target=values.pending
    )
    def pending(self):
        try:
            self.instance.donation.transitions.succeed()
            self.instance.donation.save()
            self.instance.donation.activity.update_amounts()
        except TransitionNotPossible:
            pass

    @transition(
        source=[values.charged, values.pending],
        target=values.succeeded
    )
    def succeed(self):
        try:
            self.instance.donation.transitions.succeed()
            self.instance.donation.save()
            self.instance.donation.activity.update_amounts()
        except TransitionNotPossible:
            pass

    @transition(
        source=[values.new, values.charged, values.succeeded],
        target='failed'
    )
    def fail(self):
        self.instance.donation.transitions.fail()
        self.instance.donation.save()
        self.instance.donation.activity.update_amounts()

    @transition(
        source=[values.succeeded],
        target=PaymentTransitions.values.refund_requested
    )
    def request_refund(self):
        try:
            self.instance.refund()
        except StripeError as error:
            raise PaymentException(error.message)

    @transition(
        source=[values.new],
        target=values.charged,
        conditions=[has_charge_token]
    )
    def charge(self):
        pass

    @transition(
        source=[values.new],
        target=values.canceled,
    )
    def cancel(self):
        self.instance.donation.transitions.fail()
        self.instance.donation.save()
        self.instance.donation.activity.update_amounts()

    @transition(
        source=[values.succeeded],
        target=values.disputed,
    )
    def dispute(self):
        if self.instance.donation.status != 'refunded':
            self.instance.donation.transitions.refund()
            self.instance.donation.save()
        self.instance.donation.activity.update_amounts()


class StripePayoutAccountTransitions(PayoutAccountTransitions):
    @transition(
        source=[PayoutAccountTransitions.values.new, PayoutAccountTransitions.values.rejected],
        target=PayoutAccountTransitions.values.pending
    )
    def submit(self):
        pass

    @transition(
        source=[
            PayoutAccountTransitions.values.pending,
            PayoutAccountTransitions.values.rejected,
            PayoutAccountTransitions.values.new
        ],
        target='verified'
    )
    def verify(self):
        pass

    @transition(
        source=[PayoutAccountTransitions.values.pending, PayoutAccountTransitions.values.verified],
        target=PayoutAccountTransitions.values.rejected
    )
    def reject(self):
        pass
