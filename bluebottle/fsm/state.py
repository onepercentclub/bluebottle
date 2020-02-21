from django.utils.translation import ugettext_lazy as _
from django.dispatch import Signal


class TransitionNotPossible(Exception):
    pass


class Transition(object):
    def __init__(self, sources, target, automatic=True, conditions=None, **options):
        self.sources = sources
        self.target = target
        self.automatic = automatic
        self.conditions = conditions or []
        self.options = options

    @property
    def source_values(self):
        return [source.value for source in self.sources]

    def is_valid(self, machine):
        if not all(condition(machine) for condition in self.conditions):
            raise TransitionNotPossible(
                _('Conditions not met for transition')
            )

    def can_execute(self, machine):
        self.is_valid(machine)

        if machine.state not in self.source_values:
            raise TransitionNotPossible(
                _('Cannot transition from {}').format(machine.state)
            )

    def on_execute(self, machine):
        machine.state = self.target.value

        try:
            getattr(machine, 'on_{}'.format(self.field))()
        except AttributeError:
            pass

    def execute(self, machine, **kwargs):
        self.can_execute(machine, **kwargs)
        self.on_execute(machine, **kwargs)

    def __get__(self, instance, owner):
        if instance:
            def func(**kwargs):
                return self.execute(instance, **kwargs)

            return func
        else:
            return self

    def __repr__(self):
        return '<Transition from {} to {}>'.format(self.sources, self.target)


pre_state_transition = Signal(providing_args=['instance', 'transition', 'kwargs'])
post_state_transition = Signal(providing_args=['instance', 'transition', 'kwargs'])


class DjangoTransition(Transition):
    def __init__(self, *args, **kwargs):
        self.permission = kwargs.get('permission')
        super(DjangoTransition, self).__init__(*args, **kwargs)

    def can_execute(self, machine, user=None, **kwargs):
        result = super(DjangoTransition, self).can_execute(machine)

        if self.permission and user and not self.permission(machine, user):
            raise TransitionNotPossible(
                _('You are not allowed to perform this transition')
            )

            return result and (not user or self.permission(machine, user))
        else:
            return result

    def on_execute(self, machine, save=False, **kwargs):
        pre_state_transition.send(
            sender=machine.instance.__class__,
            instance=machine.instance,
            transition=self,
            **kwargs
        )

        super(DjangoTransition, self).on_execute(machine)

        if save:
            machine.save()

        post_state_transition.send(
            sender=machine.instance.__class__,
            instance=machine.instance,
            transition=self,
            **kwargs
        )


class CombinedStates(object):
    def __init__(self, states, transition_class):
        self.states = states
        self.transition_class = transition_class

    def __or__(self, other):
        return CombinedStates(self.states + [other], self.transition_class)

    def to(self, target, **kwargs):
        return self.transition_class(self.states, target, **kwargs)


class State(object):
    transition_class = DjangoTransition

    def __init__(self, name, value=None):
        self.name = name
        self.value = value

    def to(self, target, **kwargs):
        return self.transition_class([self], target, **kwargs)

    def __or__(self, other):
        return CombinedStates([self, other], self.transition_class)

    def __repr__(self):
        return '<State {}>'.format(self.name)


class EmptyState(State):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmptyState, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        super(EmptyState, self).__init__('empty', '')

    def __repr__(self):
        return '<EmptyState {}>'.format(self.name)


class StateMachineMeta(type):
    def __new__(cls, name, bases, dct):
        result = type.__new__(cls, name, bases, dct)

        states = dict(
            (key, getattr(result, key))
            for key in dir(result)
            if isinstance(getattr(result, key), State) and key != 'initial'
        )
        result.states = states

        transitions = dict(
            (key, getattr(result, key))
            for key in dir(result)
            if isinstance(getattr(result, key), Transition)
        )
        for key, transition in transitions.items():
            transition.field = key

        result.transitions = transitions

        return result


class StateMachine(object):
    __metaclass__ = StateMachineMeta

    def __init__(self):
        if self.state == '':
            initial_transitions = [
                transition
                for transition in self.transitions.values()
                if EmptyState() in transition.sources
            ]
            if (len(initial_transitions)) > 1:
                raise AssertionError(
                    'Found multiple transitions from empty state'
                )

            if initial_transitions:
                getattr(self, initial_transitions[0].field)()

    def possible_transitions(self, **kwargs):
        result = []
        for transition in self.transitions.values():
            try:
                transition.can_execute(self, **kwargs)
                result.append(transition)
            except TransitionNotPossible:
                pass

        return result

    @property
    def automatic_transition(self):
        automatic_transitions = [
            transition for transition in self.possible_transitions()
            if transition.automatic
        ]

        if len(automatic_transitions) == 1:
            return automatic_transitions[0]

    def transition(self, save=False):
        while self.automatic_transition:
            getattr(self, self.automatic_transition.field)(save=save)


class ProxiedStateMachine(StateMachine):
    def __init__(self, instance, field):
        self.instance = instance
        self.field = field

        super(ProxiedStateMachine, self).__init__()

    @property
    def state(self):
        return getattr(self.instance, self.field)

    @state.setter
    def state(self, state):
        setattr(self.instance, self.field, state)

    def save(self):
        self.instance.save()


class StateManager(object):
    def __init__(self, machine_class, field):
        self.machine_class = machine_class
        self.field = field

    def contribute_to_class(self, cls, name):
        if not hasattr(cls, '_state_machines'):
            cls._state_machines = []

        if name not in cls._state_machines:
            cls._state_machines.insert(0, name)
        setattr(cls, name, self)

    def __get__(self, instance, owner):
        if instance:
            return self.machine_class(instance, self.field)
        else:
            return self


class AutomaticStateTransitionMixin(object):
    def save(self, *args, **kwargs):
        for field in self._state_machines:
            getattr(self, field).transition()

        super(AutomaticStateTransitionMixin, self).save(*args, **kwargs)
