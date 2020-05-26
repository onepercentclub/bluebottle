from bluebottle.activities.models import Activity
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit')]

    @property
    def is_valid(self):
        "There are no errors or missing fields"
        return (
            not list(self.instance.errors) and
            not list(self.instance.required) and
            self.instance.status != ActivityStateMachine.needs_work.value
        )


Activity.triggers = [Complete]
