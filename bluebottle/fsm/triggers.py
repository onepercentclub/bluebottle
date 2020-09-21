from builtins import str
from builtins import zip
from builtins import object
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class ModelTrigger(object):
    def __init__(self, instance):
        self.instance = instance

    @property
    def is_valid(self):
        return False

    @property
    def current_effects(self):
        for effect_class in self.effects:
            effect = effect_class(self.instance)

            if effect.is_valid:
                yield effect

    def __str__(self):
        return str(_("Model has been changed"))


class ModelChangedTrigger(ModelTrigger):
    field = None

    @property
    def title(self):
        return 'change the {}'.format(self.field)

    @property
    def is_valid(self):
        if not self.field:
            return True
        return self.instance.field_is_changed(self.field)

    def __str__(self):
        if self.field:
            field_name = self.instance._meta.get_field(self.field).verbose_name
            return str(_("{} has been changed").format(field_name.capitalize()))
        return str(_("Object has been changed"))


class ModelDeletedTrigger(ModelTrigger):
    def __init__(self, instance):
        self.instance = instance

    @property
    def is_valid(self):
        pass

    def __str__(self):
        return str(_("Model has been deleted"))


class TriggerMixin(object):
    triggers = []
    periodic_tasks = []

    def __init__(self, *args, **kwargs):
        super(TriggerMixin, self).__init__(*args, **kwargs)
        self._effects = []

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

    @property
    def current_triggers(self):
        for trigger in self.triggers:
            if trigger(self).is_valid:
                yield trigger(self)

    @property
    def current_effects(self):
        for trigger in self.current_triggers:
            for effect in trigger.current_effects:
                yield effect

    @property
    def all_effects(self):
        result = []
        for current_effect in self.current_effects:
            for effect in current_effect.all_effects():
                if effect not in result:
                    result.append(effect)
        return result

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super(TriggerMixin, cls).from_db(db, field_names, values)
        instance._initial_values = dict(list(zip(field_names, values)))

        return instance

    def field_is_changed(self, field):
        return self._initial_values.get(field) != getattr(self, field)

    def save(self, send_messages=True, perform_effects=True, *args, **kwargs):
        if perform_effects and hasattr(self, '_state_machines'):
            for machine_name in self._state_machines:
                machine = getattr(self, machine_name)
                if not machine.state and machine.initial_transition:
                    machine.initial_transition.execute(machine)

            effects = self._effects + self.all_effects
        else:
            effects = []

        for effect in effects:
            effect.do(post_save=False, send_messages=send_messages)

        super(TriggerMixin, self).save(*args, **kwargs)

        for effect in effects:
            effect.do(post_save=True, send_messages=send_messages)

        self._effects = []

    def delete(self, *args, **kwargs):
        for trigger in self.triggers:
            if issubclass(trigger, ModelDeletedTrigger):
                for current_effect in trigger(self).current_effects:
                    for effect in current_effect.all_effects():
                        effect.do(post_save=True)

        return super(TriggerMixin, self).delete(*args, **kwargs)
