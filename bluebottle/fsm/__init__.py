from functools import partial

from django.db import models
from django.dispatch import Signal

pre_transition = Signal(providing_args=['instance', 'name', 'source', 'target', 'options', 'kwargs'])
post_transition = Signal(providing_args=['instance', 'name', 'source', 'target', 'options', 'kwargs'])


class TransitionNotAllowed(Exception):
    """Exception that is raised when a transition that is not allowed in the current state
    is tried.
    """


class Transition(object):
    """
    Object that represent FSM transitions

        `source`: A list of sources the transition can start from
        `target`: the target of the transtion
        `method`: the actual transition method
        `conditions`: conditions that need to hold for the transition to be possible
        `options`: extra arguments passed when defining the transition
    """
    def __init__(self, name, source, target, method, conditions=None, options=None):
        self.name = name
        if not isinstance(source, list):
            source = [source]

        self.source = source
        self.target = target
        self.method = method
        self.conditions = conditions or []
        self.options = options or {}

    def __call__(self, instance, transitions, *args, **kwargs):
        original_source = getattr(instance, transitions.field.name)  # Keep current status so we can revert

        if not self.is_allowed(instance):
            # The transition is not currently possible
            raise TransitionNotAllowed(
                'Not allowed to transition from {} to {}'.format(
                    original_source, self.target
                )
            )

        # Trigger pre_transition (still with the old value
        pre_transition.send(
            sender=instance.__class__,
            instance=instance,
            transition=self,
            **kwargs
        )

        transitions.transition_to(instance, self.target)

        try:
            self.method(transitions, instance)
            post_transition.send(
                sender=self.__class__,
                instance=instance,
                transition=self,
                **kwargs
            )
        except Exception:
            # the transition failed. Revert the value
            transitions.transition_to(instance, original_source)
            raise

    def is_allowed(self, instance):
        """ Check if the initiative is allowed currently. """
        return all(condition(instance) is None for condition in self.conditions)

    def errors(self, instance):
        """ Errors that prevent the transition """
        for condition in self.conditions:
            error = condition(instance)

            if error:
                if isinstance(error, (list, tuple)):
                    for e in error:
                        yield e
                else:
                    yield error


def transition(source, target, conditions=None, **kwargs):
    """ Decorator that creates transition functions

    Example:

    class ExampleTransitions(fsm.Transitions):
        @transition(
            source='new'
            target='test'
        )
        def test(self):
            pass
    """
    def inner_transition(func):
        # Store the transition on the field
        transition = Transition(
            func.__name__, source, target, func, conditions, kwargs
        )

        return transition

    return inner_transition


class TransitionProxy(object):
    def __init__(self, instance, transitions):
        self.instance = instance
        self.transitions = transitions

    def __getattr__(self, attr):
        value = getattr(self.transitions, attr)
        if isinstance(value, Transition):
            return partial(value, self.instance, self.transitions)
        else:
            return value


class ModelTransitions(object):
    def __init__(self, field):
        self.field = field

    def transition_to(self, instance, target):
        setattr(instance, self.field.name, target)

    def contribute_to_class(self, cls, name):
        @property
        def transitions(instance):
            return TransitionProxy(instance, self)

        setattr(cls, name, transitions)

    @property
    def all_transitions(self):
        return [
            transition for transition in self.transitions
            if '*' in transition.source or getattr(self.instance, self.name) in transition.source
        ]

    @property
    def available_transitions(self):
        return [
            transition for transition in self.all_transitions if
            transition.is_allowed(self.instance)
        ]


class FSMFieldDescriptor(object):
    """ Descriptor makes it possible to prevent direct modification of the field """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, type=None):
        """ If called on a class, return the field, so that we can access the
        transition decorator on the field.

        If called on an instance, return the current value
        """
        if instance is None:
            return self.field
            raise AttributeError('FSMFields should not be accessed on the class')

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        """
        Prevent modification of the field.
        """
        instance.__dict__[self.field.name] = value


class FSMField(models.CharField):
    """ Model field that prevents direct transitions and exposes a transition decorator. """

    def __init__(self, protected=True, max_length=20, *args, **kwargs):
        self.protected = protected

        return super(FSMField, self).__init__(
            max_length=max_length,
            *args,
            **kwargs
        )

    def contribute_to_class(self, cls, name, **kwargs):
        """ Add several fields to the model class.

        Make sure `model.<field>` is an FSMFieldDescriptor

        expose _transition_to that makes it possible to change the field
        expose get_all_transitions. This returns all transitions for the currenct value
        expose get_available_transitions. This returns all transitions where the conditions hold
        """
        super(FSMField, self).contribute_to_class(cls, name, **kwargs)

        descriptor = FSMFieldDescriptor(self)
        setattr(cls, self.name, descriptor)

    def transition(self, *args, **kwargs):
        def inner(func):
            return func

        return inner
