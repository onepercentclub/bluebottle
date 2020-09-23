
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


from bluebottle.fsm.state import pre_state_transition


class Trigger(object):
    def __init__(self, instance):
        self.instance = instance

    def execute(self, effects, **options):
        for effect_cls in self.effects:
            effect = effect_cls(self.instance, **options)

            if effect.is_valid and effect not in effects:
                effect.pre_save(effects=effects)
                if effect.post_save:
                    self.instance._postponed_effects.insert(0, effect)
                effects.append(effect)

        return effects

    def __unicode__(self):
        return unicode(_("Model has been changed"))


class ModelChangedTrigger(Trigger):
    field = None

    @ property
    def title(self):
        return 'change the {}'.format(self.field)

    @ property
    def changed(self):
        return self.instance._initial_values.get(self.field) != getattr(self.instance, self.field)

    def __unicode__(self):
        if self.field:
            field_name = self.instance._meta.get_field(self.field).verbose_name
            return unicode(_("{} has been changed").format(field_name.capitalize()))
        return unicode(_("Object has been changed"))


class ModelDeletedTrigger(Trigger):
    def __init__(self, instance):
        self.instance = instance

    def __unicode__(self):
        return unicode(_("Model has been deleted"))


class TransitionTrigger(Trigger):
    def __init__(self, instance):
        self.instance = instance

    def __unicode__(self):
        return unicode(_("Model has changed status"))

    @property
    def title(self):
        import ipdb
        ipdb.set_trace()


@ receiver(pre_state_transition)
def transition_trigger(sender, instance, transition, **kwargs):
    if issubclass(sender, TriggerMixin) and hasattr(instance, 'triggers'):
        for trigger in instance.triggers:
            if issubclass(trigger, TransitionTrigger) and trigger.transition == transition:
                instance._triggers.append(trigger(instance))


def register(model_cls):
    def _register(trigger):
        if not hasattr(model_cls, 'triggers'):
            model_cls.triggers = []

        model_cls.triggers.append(trigger)

        return trigger

    return _register


class TriggerMixin(object):
    periodic_tasks = []

    def __init__(self, *args, **kwargs):
        super(TriggerMixin, self).__init__(*args, **kwargs)
        self._triggers = []
        self._postponed_effects = []
        self._transitions = []

        if hasattr(self, '_state_machines'):
            for name, machine_class in self._state_machines.items():
                machine = machine_class(self)

                setattr(self, name, machine)

        self._initial_values = dict(
            (field.name, getattr(self, field.name))
            for field in self._meta.fields
            if not field.is_relation
        )

    @ classmethod
    def get_periodic_tasks(cls):
        result = []
        for task in cls.periodic_tasks:
            result.append(task(cls))
        return result

    @ classmethod
    def from_db(cls, db, field_names, values):
        instance = super(TriggerMixin, cls).from_db(db, field_names, values)
        instance._initial_values = dict(zip(field_names, values))

        return instance

    def _check_model_changed_triggers(self):
        if hasattr(self, 'triggers'):
            for trigger_cls in self.triggers:
                if issubclass(trigger_cls, ModelChangedTrigger):
                    trigger = trigger_cls(self)
                    if trigger.changed:
                        self._triggers.append(trigger)

    def execute_triggers(self, effects=None, **options):
        if hasattr(self, '_state_machines'):
            for machine_name in self._state_machines:
                machine = getattr(self, machine_name)
                if not machine.state and machine.initial_transition:
                    machine.initial_transition.execute(machine)

        self._check_model_changed_triggers()

        if not effects:
            effects = []

        while self._triggers:
            trigger = self._triggers.pop()
            trigger.execute(effects, **options)

        return effects

    def save(self, *args, **kwargs):
        self.execute_triggers()

        super(TriggerMixin, self).save(*args, **kwargs)

        while self._postponed_effects:
            effect = self._postponed_effects.pop()
            effect.post_save()

    def delete(self, *args, **kwargs):
        for trigger in self.triggers:
            if issubclass(trigger, ModelDeletedTrigger):
                trigger(self).execute([])

        return super(TriggerMixin, self).delete(*args, **kwargs)
