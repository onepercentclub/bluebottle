from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit', 'review_states')]

    @property
    def is_valid(self):
        "There are no errors or missing fields"
        return (
            not list(self.instance.errors) and
            not list(self.instance.required)
        )
