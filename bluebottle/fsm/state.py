from builtins import object
from builtins import str

from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _
from future.utils import with_metaclass


class TransitionNotPossible(Exception):
    pass


def register(model_cls):
    def _register(state_machine_cls):
        if not hasattr(model_cls, '_state_machines'):
            model_cls._state_machines = {}
        else:
            model_cls._state_machines = dict(model_cls._state_machines)

        model_cls._state_machines[state_machine_cls.name] = state_machine_cls
        return state_machine_cls

    return _register


class BaseTransition(object):
    def __init__(
        self,
        sources,
        target,
        name="",
        description="",
        description_front_end="",
        short_description=None,
        passed_label=None,
        automatic=True,
        conditions=None,
        effects=None,
        **options
    ):
        self.name = name

        if not isinstance(sources, (list, tuple)):
            sources = (sources, )

        self.sources = sources
        self.target = target
        self.automatic = automatic
        self.conditions = conditions or []
        self.effects = effects or []
        self.description = description
        self.short_description = short_description
        self.description_front_end = description_front_end or description

        self.passed_label = passed_label

        assert not (
            not self.automatic and not self.name), 'Automatic transitions should have a name'

        self.options = options

    @property
    def source_values(self):
        return [source.value for source in self.sources]

    def is_valid(self, machine):
        if not all(condition(machine) for condition in self.conditions):
            raise TransitionNotPossible(
                _('Conditions not met for transition')
            )

    def can_execute(self, machine, automatic=True, **kwargs):
        self.is_valid(machine)
        if not automatic and self.automatic:
            raise TransitionNotPossible(
                _('Cannot transition from {} to {}').format(
                    machine.state, self.target)
            )

        if not (
            machine.state in self.source_values or
            (AllStates() in self.sources)
        ):
            raise TransitionNotPossible(
                _('Cannot transition from {} to {}').format(
                    machine.state, self.target)
            )

    def on_execute(self, machine):
        machine.state = self.target.value

    def execute(self, machine, **kwargs):
        self.can_execute(machine, **kwargs)
        self.on_execute(machine, **kwargs)

    def __get__(self, instance, owner):
        if instance and isinstance(instance, StateMachine):
            def func(**kwargs):
                return self.execute(instance, **kwargs)

            return func
        else:
            return self

    def __repr__(self):
        return '<Transition from {} to {}>'.format(self.sources, self.target)

    def __str__(self):
        return str(self.name or self.field)


pre_state_transition = Signal(
    providing_args=['instance', 'transition', 'kwargs'])
post_state_transition = Signal(
    providing_args=['instance', 'transition', 'kwargs'])


class Transition(BaseTransition):
    def __init__(self, sources, target, *args, **kwargs):
        self.permission = kwargs.get('permission')
        super(Transition, self).__init__(sources, target, *args, **kwargs)

    def can_execute(self, machine, user=None, **kwargs):
        result = super(Transition, self).can_execute(machine, **kwargs)

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

        super(Transition, self).on_execute(machine)

        if save:
            machine.save()

        post_state_transition.send(
            sender=machine.instance.__class__,
            instance=machine.instance,
            transition=self,
            **kwargs
        )


class State(object):
    transition_class = Transition

    def __init__(self, name, value=None, description='', description_front_end=''):
        self.name = name
        self.value = value
        self.description = description
        self.description_front_end = description_front_end or description

    def __repr__(self):
        return '<State {}>'.format(self.name)

    def __str__(self):
        return str(self.name)


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


class AllStates(State):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AllStates, cls).__new__(
                cls, *args, **kwargs)

        return cls._instance

    def __init__(self):
        super(AllStates, self).__init__('all', '')

    def __repr__(self):
        return '<All States {}>'.format(self.name)


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
        for key, transition in list(transitions.items()):
            transition.field = key

        result.transitions = transitions

        return result


class StateMachine(with_metaclass(StateMachineMeta, object)):
    @property
    def initial_transition(self):
        initial_transitions = [
            transition
            for transition in list(self.transitions.values())
            if EmptyState() in transition.sources
        ]
        if (len(initial_transitions)) > 1:
            raise AssertionError(
                'Found multiple transitions from empty state'
            )

        if initial_transitions:
            return initial_transitions[0]

    @property
    def current_state(self):
        for state in list(self.states.values()):
            if state.value == self.state:
                return state

    def possible_transitions(self, **kwargs):
        result = []
        for transition in list(self.transitions.values()):
            try:
                transition.can_execute(self, **kwargs)
                result.append(transition)
            except TransitionNotPossible:
                pass

        return result


class ModelStateMachineMeta(StateMachineMeta):
    def __new__(cls, name, bases, dct):
        if 'field' not in dct:
            dct['field'] = 'status'

        if 'name' not in dct:
            dct['name'] = 'states'

        return StateMachineMeta.__new__(cls, name, bases, dct)


class ModelStateMachine(with_metaclass(ModelStateMachineMeta, StateMachine)):
    def __init__(self, instance):
        self.instance = instance

        super(ModelStateMachine, self).__init__()

    @property
    def state(self):
        return getattr(self.instance, self.field)

    @state.setter
    def state(self, state):
        setattr(self.instance, self.field, state)

    def save(self):
        self.instance.save()
