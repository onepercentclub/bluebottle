
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


from bluebottle.fsm.state import pre_state_transition


class TriggerManager(object):
    pass


class BoundTrigger(object):
    def __init__(self, instance, trigger):
        self.instance = instance
        self.trigger = trigger

    def execute(self, previous_effects, **options):
        return self.trigger.execute(self.instance, previous_effects, **options)


class Trigger(object):
    def __init__(self, effects=None):
        if effects is None:
            effects = []

        self.effects = effects

    def execute(self, instance, previous_effects, **options):
        for effect_cls in self.effects:
            effect = effect_cls(instance, **options)

            if effect.is_valid and effect not in previous_effects:
                effect.pre_save(effects=previous_effects)
                if effect.post_save:
                    instance._postponed_effects.insert(0, effect)
                previous_effects.append(effect)

        return previous_effects

    def __unicode__(self):
        return unicode(_("Model has been changed"))


class ModelChangedTrigger(Trigger):
    def __init__(self, field, *args, **kwargs):
        super(ModelChangedTrigger, self).__init__(*args, **kwargs)
        self.field = field

    @ property
    def title(self):
        return 'change the {}'.format(self.field)

    def changed(self, instance):
        return instance._initial_values.get(self.field) != getattr(instance, self.field)

    def __unicode__(self):
        if self.field:
            field_name = self.instance._meta.get_field(self.field).verbose_name
            return unicode(_("{} has been changed").format(field_name.capitalize()))
        return unicode(_("Object has been changed"))


class ModelDeletedTrigger(Trigger):
    def __unicode__(self):
        return unicode(_("Model has been deleted"))


class TransitionTrigger(Trigger):
    def __init__(self, transition, *args, **kwargs):
        super(TransitionTrigger, self).__init__(*args, **kwargs)
        self.transition = transition

    def __unicode__(self):
        return unicode(_("Model has changed status"))

    @property
    def title(self):
        import ipdb
        ipdb.set_trace()


@ receiver(pre_state_transition)
def transition_trigger(sender, instance, transition, **kwargs):
    if issubclass(sender, TriggerMixin) and hasattr(instance, 'triggers'):
        for trigger in instance.triggers.triggers:
            if isinstance(trigger, TransitionTrigger) and trigger.transition == transition:
                instance._triggers.append(BoundTrigger(instance, trigger))


def register(model_cls):
    def _register(TriggerManager):
        model_cls.triggers = TriggerManager()

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
            for trigger in self.triggers.triggers:
                if isinstance(trigger, ModelChangedTrigger):
                    if trigger.changed(self):
                        self._triggers.append(BoundTrigger(self, trigger))

    def execute_triggers(self, effects=None, **options):
        if hasattr(self, '_state_machines'):
            for machine_name in self._state_machines:
                machine = getattr(self, machine_name)
                if not machine.state and machine.initial_transition:
                    machine.initial_transition.execute(machine)

        self._check_model_changed_triggers()

        if effects is None:
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
        if hasattr(self, 'triggers'):
            for trigger in self.triggers.triggers:
                if isinstance(trigger, ModelDeletedTrigger):
                    BoundTrigger(self, trigger).execute([])

        return super(TriggerMixin, self).delete(*args, **kwargs)
