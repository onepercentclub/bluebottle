from django.utils.translation import ugettext_lazy as _
from django.dispatch import Signal


class TransitionNotPossible(Exception):
    pass


class BaseTransition(object):
    def __init__(self, sources, target, name=None, automatic=True, conditions=None, effects=None, **options):
        self.name = name

        if not isinstance(sources, (list, tuple)):
            sources = (sources, )

        self.sources = sources
        self.target = target
        self.automatic = automatic
        self.conditions = conditions or []
        self.effects = effects or []

        assert not (not self.automatic and not self.name), 'Automatic transitions should have a name'

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
                _('Cannot transition from {} to {}').format(machine.state, self.target)
            )

        if machine.state not in self.source_values and AllStates() not in self.sources:
            raise TransitionNotPossible(
                _('Cannot transition from {} to {}').format(machine.state, self.target)
            )

    def on_execute(self, machine):
        machine.state = self.target.value

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

    def __unicode__(self):
        return unicode(self.name or self.field)


pre_state_transition = Signal(providing_args=['instance', 'transition', 'kwargs'])
post_state_transition = Signal(providing_args=['instance', 'transition', 'kwargs'])


class Transition(BaseTransition):
    def __init__(self, sources, target, *args, **kwargs):
        self.permission = kwargs.get('permission')
        super(Transition, self).__init__(sources, target, *args, **kwargs)

    def can_execute(self, machine, user=None, **kwargs):
        result = super(Transition, self).can_execute(machine, **kwargs)

        if self.permission and user and not user.is_staff and not self.permission(machine, user):
            raise TransitionNotPossible(
                _('You are not allowed to perform this transition')
            )

            return result and (not user or self.permission(machine, user))
        else:
            return result

    def on_execute(self, machine, save=False, effects=True, **kwargs):
        pre_state_transition.send(
            sender=machine.instance.__class__,
            instance=machine.instance,
            transition=self,
            **kwargs
        )

        super(Transition, self).on_execute(machine)

        for effect in self.effects:
            machine.instance._effects += effect(machine.instance, **kwargs).all_effects()

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

    def __init__(self, name, value=None, description=''):
        self.name = name
        self.value = value
        self.description = description

    def __repr__(self):
        return '<State {}>'.format(self.name)

    def __unicode__(self):
        return unicode(self.name)


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
        for key, transition in transitions.items():
            transition.field = key

        result.transitions = transitions

        return result


class StateMachine(object):
    __metaclass__ = StateMachineMeta

    @property
    def initial_transition(self):
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
            return initial_transitions[0]

    @property
    def current_state(self):
        for state in self.states.values():
            if state.value == self.state:
                return state

    def possible_transitions(self, **kwargs):
        result = []
        for transition in self.transitions.values():
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

        result = StateMachineMeta.__new__(cls, name, bases, dct)

        if hasattr(result, 'model'):
            if not hasattr(result.model, '_state_machines'):
                result.model._state_machines = {}

            result.model._state_machines[result.name] = result

        return result


class ModelStateMachine(StateMachine):
    __metaclass__ = ModelStateMachineMeta

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
