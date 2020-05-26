from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.initiatives.models import Initiative


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit')]

    @property
    def is_valid(self):
        "There are no errors or missing fields"
        from bluebottle.initiatives.states import ReviewStateMachine
        return (
            not list(self.instance.errors) and
            not list(self.instance.required) and
            self.instance.status != ReviewStateMachine.needs_work.value
        )


Initiative.triggers = [Complete]
