from builtins import str
from builtins import object
from builtins import zip
from operator import ipow

from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user
from future.utils import python_2_unicode_compatible
from django.template.loader import render_to_string

from bluebottle.fsm.state import pre_state_transition
from bluebottle.fsm.effects import Effect


class TriggerManager(object):
    pass


class BoundTrigger(object):
    def __init__(self, instance, trigger):
        self.instance = instance
        self.trigger = trigger

    def execute(self):
        return self.trigger.execute(self.instance)


@python_2_unicode_compatible
class Trigger(object):
    def __init__(self, effects=None):
        if effects is None:
            effects = []

        self.effects = effects

    def execute(self, instance):
        for effect_cls in self.effects:
            effect = effect_cls(instance)

            if effect.is_valid:
                effect.execute()


    def __str__(self):
        return str(_("Model has been changed"))


@python_2_unicode_compatible
class ModelChangedTrigger(Trigger):
    def __init__(self, fields, *args, **kwargs):
        super(ModelChangedTrigger, self).__init__(*args, **kwargs)
        if not isinstance(fields, (tuple, list)):
            fields = (fields, )
        self.fields = fields

    @property
    def title(self):
        return 'change the {}'.format(
            ', '.join(field.capitalize() for field in self.fields)
        )

    def changed(self, instance):
        return any(
            instance._initial_values.get(field) != getattr(instance, field)
            for field in self.fields
        )

    def __str__(self):
        if self.fields:
            return _("{} has been changed").format(
                ', '.join(field.capitalize() for field in self.fields)
            )
        return str(_("Object has been changed"))


class ModelDeletedTrigger(Trigger):
    def __str__(self):
        return str(_("Model has been deleted"))


class ModelCreatedTrigger(Trigger):
    def __str__(self):
        return str(_("Model has been created"))


@receiver(pre_delete)
def pre_delete_trigger(sender, instance, **kwargs):
    if issubclass(sender, TriggerMixin) and hasattr(instance, 'triggers'):
        for trigger in instance.triggers.triggers:
            if isinstance(trigger, ModelDeletedTrigger):
                BoundTrigger(instance, trigger).execute()


@python_2_unicode_compatible
class TransitionTrigger(Trigger):
    def __init__(self, transition, *args, **kwargs):
        super(TransitionTrigger, self).__init__(*args, **kwargs)
        self.transition = transition

    def __str__(self):
        return str(_("Model has changed status"))

    def title(self):
        return "MISSING TITLE"


def register(model_cls):
    def _register(TriggerManager):
        model_cls.triggers = TriggerManager()
        return TriggerManager

    return _register


class TransitionEffect(Effect):
    def __init__(self, instance, transition):
        self.transition = transition
        super().__init__(instance)

    def execute(self):
        print(
            f"transition {self.instance} to {self.transition} from {self.instance.status}"
        )
        self.transition.execute(self.instance.states)
        super().execute()

    def __str__(self):
        return "Transition"

    template = "admin/transition_effect.html"

    @classmethod
    def render(cls, effects):
        final_transition = effects[-1].transition.target
        context = {
            "opts": effects[0].instance.__class__._meta,
            "effects": [
                effect
                for effect in effects
                if effect.transition.target == final_transition
            ],
        }
        return render_to_string(cls.template, context)

class TriggerMixin(object):
    periodic_tasks = []

    def __copy__(self):
        result = self.__class__.__new__(self.__class__)
        result.__dict__.update(self.__dict__)

        # create a new statemachine when copying models.
        # Without this model.states.instance still points to the old model,
        # and state changes are only reflected on the old model.
        for name, machine_class in list(result._state_machines.items()):
            machine = machine_class(result)

            setattr(result, name, machine)

        return result

    def __init__(self, *args, **kwargs):
        super(TriggerMixin, self).__init__(*args, **kwargs)

        if hasattr(self, '_state_machines'):
            for name, machine_class in list(self._state_machines.items()):
                machine = machine_class(self)

                setattr(self, name, machine)

        self._initial_values = dict(
            (field.name, getattr(self, field.name))
            for field in self._meta.fields
            if not field.is_relation
        )

    @classmethod
    def get_periodic_tasks(cls):
        result = []
        for task in cls.periodic_tasks:
            result.append(task(cls))
        return result

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super(TriggerMixin, cls).from_db(db, field_names, values)
        instance._initial_values = dict(list(zip(field_names, values)))

        return instance

    def _check_model_changed_triggers(self):
        if hasattr(self, 'triggers'):
            for trigger in self.triggers.triggers:
                if isinstance(trigger, ModelChangedTrigger):
                    if trigger.changed(self):
                        self._triggers.append(BoundTrigger(self, trigger))

    def _execute_triggers(self):
        if hasattr(self, '_state_machines'):
            for machine_name in self._state_machines:
                machine = getattr(self, machine_name)
                if not machine.state and machine.initial_transition:
                    machine.initial_transition.execute(machine)

        while self.states.automatic_transitions():
            transition = self.states.automatic_transitions()[0]
            effect = TransitionEffect(self, transition)
            effect.execute()

    def save(self, *args, **kwargs):
        self._execute_triggers()

        super(TriggerMixin, self).save(*args, **kwargs)

        for instance in self.states.related_models:
            if instance.states.automatic_transitions():
                instance.save()

        self._initial_values = dict(
            (field.name, getattr(self, field.name))
            for field in self._meta.fields
            if not field.is_relation
        )


from bluebottle.fsm.signals import *
