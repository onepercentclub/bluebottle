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


class ModelChangedTrigger(ModelTrigger):
    field = None

    @property
    def is_valid(self):
        return self.instance.field_is_changed(self.field)


class ModelDeletedTrigger(ModelTrigger):
    def __init__(self, instance):
        self.instance = instance

    @property
    def is_valid(self):
        pass


class TriggerMixin(object):
    triggers = []

    def __init__(self, *args, **kwargs):
        super(TriggerMixin, self).__init__(*args, **kwargs)
        self._effects = []

        if hasattr(self, '_state_machines'):
            for name, machine_class in self._state_machines.items():
                machine = machine_class(self)

                setattr(self, name, machine)

        self._initial_values = dict(
            (field.name, getattr(self, field.name))
            for field in self._meta.fields
            if not field.is_relation
        )

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
        instance._initial_values = dict(zip(field_names, values))

        return instance

    def field_is_changed(self, field):
        return self._initial_values.get(field) != getattr(self, field)

    def save(self, send_messages=True, perform_effects=True, *args, **kwargs):
        if perform_effects:
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
            effect.do(post_save=True)

        self._effects = []

    def delete(self, *args, **kwargs):
        for trigger in self.triggers:
            if issubclass(trigger, ModelDeletedTrigger):
                for current_effect in trigger(self).current_effects:
                    for effect in current_effect.all_effects():
                        effect.do(post_save=True)

        return super(TriggerMixin, self).delete(*args, **kwargs)
