from builtins import str
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.funding.models import Funding
from bluebottle.funding.states import FundingStateMachine


class FundingFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            deadline__lte=timezone.now(),
            status='open'
        )

    effects = [
        TransitionEffect('succeed', conditions=[
            FundingStateMachine.target_reached
        ]),
        TransitionEffect('partial', conditions=[
            FundingStateMachine.target_not_reached
        ]),
        TransitionEffect('expire', conditions=[
            FundingStateMachine.no_donations
        ]),
    ]

    def __str__(self):
        return str(_("Campaign deadline has passed."))


Funding.periodic_tasks = [FundingFinishedTask]
