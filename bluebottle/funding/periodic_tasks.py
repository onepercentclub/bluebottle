from datetime import timedelta
from builtins import str
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.funding.models import Funding, Donor
from bluebottle.funding.states import FundingStateMachine, DonorStateMachine


def target_reached(effect):
    """target amount has been reached (100% or more)"""
    if not effect.instance.target:
        return False
    return effect.instance.amount_raised >= effect.instance.target


def target_not_reached(effect):
    """target amount has not been reached (less then 100%, but more then 0)"""
    return effect.instance.amount_raised.amount and effect.instance.amount_raised < effect.instance.target


def no_donations(effect):
    """no (successful) donations have been made"""
    return not effect.instance.donations.filter(status='succeeded').count()


class FundingFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            deadline__lte=timezone.now(),
            status='open'
        )

    effects = [
        TransitionEffect(FundingStateMachine.succeed, conditions=[
            target_reached
        ]),
        TransitionEffect(FundingStateMachine.partial, conditions=[
            target_not_reached
        ]),
        TransitionEffect(FundingStateMachine.expire, conditions=[
            no_donations
        ]),
    ]

    def __str__(self):
        return str(_("Campaign deadline has passed."))


class DonorExpiredTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            created__lte=timezone.now() - timedelta(days=14),
            status='new'
        )

    effects = [
        TransitionEffect(DonorStateMachine.expire)
    ]

    def __str__(self):
        return str(_("Campaign deadline has passed."))


Funding.periodic_tasks = [FundingFinishedTask]
Donor.periodic_tasks = [DonorExpiredTask]
