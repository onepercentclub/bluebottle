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

    def is_allowed(self, transitions):
        """ Check if the initiative is allowed currently. """
        return all(condition(transitions) is None for condition in self.conditions)

    def errors(self):
        """ Errors that prevent the transition """
        for condition in self.conditions:
            error = condition()

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
        return Transition(
            func.__name__, source, target, func, conditions, kwargs
        )

    return inner_transition


class partialmethod(partial):
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self.func, instance,
                       *(self.args or ()), **(self.keywords or {}))


class ModelTransitionsMeta(type):
    def __new__(cls, name, bases, dct):
        if bases:
            dct['transitions'] = [transition for transition in getattr(bases[0], 'transitions', [])]
        else:
            dct['transitions'] = []

        for attr in dct:
            if isinstance(dct[attr], Transition):
                transition = dct[attr]
                dct['transitions'].append(transition)
                dct[attr] = partialmethod(bases[0].transition_to, transition)

        return type.__new__(cls, name, bases, dct)


class ModelTransitions():
    __metaclass__ = ModelTransitionsMeta

    def __init__(self, instance, field):
        self.instance = instance
        self.field = field

    def transition_to(self, transition, **kwargs):
        original_source = getattr(self.instance, self.field)  # Keep current status so we can revert

        if transition not in self.all_transitions or not transition.is_allowed(self):
            # The transition is not currently possible
            raise TransitionNotAllowed(
                'Not allowed to transition from {} to {}'.format(
                    original_source, transition.target
                )
            )

        # Trigger pre_transition (still with the old value
        pre_transition.send(
            sender=self.instance.__class__,
            instance=self.instance,
            transition=transition,
            **kwargs
        )

        setattr(self.instance, self.field, transition.target)

        try:
            transition.method(self)

            post_transition.send(
                sender=self.instance.__class__,
                instance=self.instance,
                transition=transition,
                **kwargs
            )
        except Exception:
            # the transition failed. Revert the value
            setattr(self.instance, self.field, transition.target)
            raise

    @property
    def all_transitions(self):
        return [
            transition for transition in self.transitions
            if (
                '*' in transition.source or
                getattr(self.instance, self.field) in transition.source
            )
        ]

    @property
    def available_transitions(self):
        return [
            transition for transition in self.all_transitions if
            transition.is_allowed(self)
        ]


class TransitionManager(object):
    def __init__(self, *args):
        self.args = args

    def contribute_to_class(self, cls, name):
        if not hasattr(cls, '_transitions'):
            cls._transitions = []

        cls._transitions.append((name, ) + self.args)


class FSMField(models.CharField):
    """ Model field that prevents direct transitions and exposes a transition decorator. """

    def __init__(self, protected=True, max_length=20, *args, **kwargs):
        self.protected = protected

        super(FSMField, self).__init__(
            max_length=max_length,
            *args,
            **kwargs
        )


class TransitionsMixin(object):
    def __init__(self, *args, **kwargs):
        if hasattr(self, '_transitions'):
            for (name, cls, field) in self._transitions:
                setattr(self, name, cls(self, field))

        super(TransitionsMixin, self).__init__(*args, **kwargs)
