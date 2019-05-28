from django.db import models


class TransitionNotAllowed(Exception):
    pass


class FSMFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, type=None):
        if instance is None:
            return self.field

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        if self.field.protected and self.field.name in instance.__dict__:
            raise AttributeError('Direct {0} modification is not allowed'.format(self.field.name))

        instance.__dict__[self.field.name] = value


class FSMField(models.CharField):
    def __init__(self, protected=True, max_length=20, *args, **kwargs):
        self.protected = protected
        self.transitions = []

        return super(FSMField, self).__init__(max_length=max_length, *args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super(FSMField, self).contribute_to_class(cls, name, **kwargs)

        descriptor = FSMFieldDescriptor(self)
        setattr(cls, self.name, descriptor)

        def transition_to(instance, value):
            instance.__dict__[self.name] = value

        setattr(cls, '_transition_{}_to'.format(self.name), transition_to)

    def get_all_transitions(self, instance):
        return [transition for transition in self.transitions if getattr(instance, self.name) in transition['source']]

    def get_all_available_transitions(self, instance):
        return [
            transition for transition in self.get_all_transitions(instance) if
            all(condition(instance) for condition in (transition.get('conditions') or []))
        ]

    def transition(field, source, target, conditions=None, **kwargs):
        field.transitions.append({
            'source': source,
            'target': target,
            'conditions': conditions,
            'kwargs': kwargs
        })

        def inner_transition(func):
            def do_transition(self):
                original_source = getattr(self, field.name)

                getattr(self, '_transition_{}_to'.format(field.name))(target)

                if conditions and not all(condition(self) for condition in conditions):
                    raise TransitionNotAllowed(
                        'Not allowed to transition from {} to {}'.format(
                            original_source, target
                        )
                    )
                try:
                    return func(self)
                except Exception:
                    getattr(self, '_transition_{}_to'.format(field.name))(original_source)
                    raise

            return do_transition

        return inner_transition
