from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod
from bluebottle.funding_pledge.transitions import PledgePaymentTransitions


class PledgePayment(Payment):
    transitions = TransitionManager(PledgePaymentTransitions, 'status')

    def save(self, *args, **kwargs):
        super(PledgePayment, self).save(*args, **kwargs)


class PledgePaymentProvider(PaymentProvider):

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='pledge',
                code='pledge',
                name=_('Pledge'),
                currencies=['EUR', 'USD']
            )
        ]


@receiver(post_save, weak=False, sender=PledgePayment)
def instant_success(sender, instance, **kwargs):
    # Use a signal for this instead of in save() so all
    # side effects of the transition are played.
    if instance.status == PledgePaymentTransitions.values.new:
        instance.transitions.succeed()
