from django.db import models


class TransitionNotAllowed(Exception):
    pass


class Transition(object):
    def __init__(self, name, source, target, method, conditions=None, options=None):
        self.name = name
        if not isinstance(source, list):
            source = [source]

        self.source = source
        self.target = target
        self.method = method
        self.conditions = conditions or []
        self.options = options or {}

    def is_allowed(self, instance):
        return all(condition(instance) is None for condition in self.conditions)


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

        def get_available_transitions(instance):
            return self.get_available_transitions(instance)

        setattr(cls, 'get_available_{}_transitions'.format(self.name), get_available_transitions)

        def get_all_transitions(instance):
            return self.get_all_transitions(instance)

        setattr(cls, 'get_all_{}_transitions'.format(self.name), get_all_transitions)

    def get_all_transitions(self, instance):
        return [
            transition for transition in self.transitions
            if '*' in transition.source or getattr(instance, self.name) in transition.source
        ]

    def get_available_transitions(self, instance):
        return [
            transition for transition in self.get_all_transitions(instance) if
            transition.is_allowed(instance)
        ]

    def transition(field, source, target, conditions=None, **kwargs):
        def inner_transition(func):
            transition = Transition(
                func.__name__, source, target, func, conditions, kwargs
            )
            field.transitions.append(transition)

            def do_transition(self):
                original_source = getattr(self, field.name)

                if not transition.is_allowed(self):
                    raise TransitionNotAllowed(
                        'Not allowed to transition from {} to {}'.format(
                            original_source, target
                        )
                    )

                getattr(self, '_transition_{}_to'.format(field.name))(target)

                try:
                    return func(self)
                except Exception:
                    getattr(self, '_transition_{}_to'.format(field.name))(original_source)
                    raise

            return do_transition

        return inner_transition
