from datetime import date

from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.voting.models import Poll
from bluebottle.voting.states import PollStateMachine


class PollDeadlinePassedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end_date__lte=date.today(),
            status='open'
        )

    effects = [
        TransitionEffect(PollStateMachine.close)
    ]

    def __str__(self):
        return str(_("Close the poll when the deadline has passed"))


Poll.periodic_tasks = [
    PollDeadlinePassedTask
]
