from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit', 'review_states')]

    @property
    def is_valid(self):
        return (
            not list(self.instance.errors) and
            not list(self.instance.required)
        )
