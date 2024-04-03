from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_delete

from builtins import str
from builtins import zip
from builtins import object
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user
from future.utils import python_2_unicode_compatible


from bluebottle.fsm.state import pre_state_transition

from threading import local


effects = local()


def get_local_effects():
    return getattr(effects, "effects", [])


def append_effect(effect):
    if hasattr(effects, "effects"):
        effects.effects = [effect] + effects.effects
    else:
        effects.effects = [effect]


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


@receiver(post_delete)
def post_delete_trigger(sender, instance, **kwargs):
    if issubclass(sender, TriggerMixin) and hasattr(instance, 'triggers'):
        while instance._postponed_effects:
            effect = instance._postponed_effects.pop()
            effect.post_save()


@python_2_unicode_compatible
class TransitionTrigger(Trigger):
    def __init__(self, transition, *args, **kwargs):
        super(TransitionTrigger, self).__init__(*args, **kwargs)
        self.transition = transition

    def __str__(self):
        return str(_("Model has changed status"))

    def title(self):
        return "MISSING TITLE"


@receiver(pre_state_transition)
def transition_trigger(sender, instance, transition, **kwargs):
    if issubclass(sender, TriggerMixin) and hasattr(instance, 'triggers'):
        for trigger in instance.triggers.triggers:
            if isinstance(trigger, TransitionTrigger) and trigger.transition == transition:
                instance._triggers.append(BoundTrigger(instance, trigger))


def register(model_cls):
    def _register(TriggerManager):
        model_cls.triggers = TriggerManager()
        return TriggerManager

    return _register


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
        self._triggers = []
        self._postponed_effects = []
        self._transitions = []

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

    def _check_model_created_triggers(self):
        if hasattr(self, 'triggers') and not self.pk:
            for trigger in self.triggers.triggers:
                if isinstance(trigger, ModelCreatedTrigger):
                    self._triggers.append(BoundTrigger(self, trigger))

    def _execute_triggers(self):
        if hasattr(self, '_state_machines'):
            for machine_name in self._state_machines:
                machine = getattr(self, machine_name)
                if not machine.state and machine.initial_transition:
                    machine.initial_transition.execute(machine)

        self._check_model_changed_triggers()
        self._check_model_created_triggers()

        while self._triggers:
            trigger = self._triggers.pop()
            trigger.execute()

        self._triggers = []

        return effects

    def save(self, run_triggers=True, *args, **kwargs):
        super(TriggerMixin, self).save(*args, **kwargs)

        if run_triggers:
            self._execute_triggers()

        self._initial_values = dict(
            (field.name, getattr(self, field.name))
            for field in self._meta.fields
            if not field.is_relation
        )
