from django.test import TestCase

from bluebottle.fsm.state import (
    AllStates,
    BaseTransition,
    EmptyState,
    ModelStateMachine,
    State,
    StateMachine,
    Transition,
    TransitionNotPossible,
)


class DraftState(State):
    def __init__(self):
        super().__init__('Draft', 'draft')


class PublishedState(State):
    def __init__(self):
        super().__init__('Published', 'published')


class DummyModel(object):
    def __init__(self, status='draft'):
        self.status = status

    def save(self):
        pass


class DummyModelStateMachine(ModelStateMachine):
    draft = DraftState()
    published = PublishedState()
    publish = Transition(
        [DraftState()],
        PublishedState(),
        name='publish',
        automatic=False,
    )


class SimpleMachine(StateMachine):
    draft = DraftState()
    published = PublishedState()


class StateMachineTestCase(TestCase):
    def test_transition_updates_state(self):
        model = DummyModel()
        machine = DummyModelStateMachine(model)
        machine.publish()
        self.assertEqual(model.status, 'published')

    def test_transition_not_possible_for_wrong_source(self):
        model = DummyModel(status='published')
        machine = DummyModelStateMachine(model)
        with self.assertRaises(TransitionNotPossible):
            machine.publish()

    def test_possible_transitions_filters_invalid(self):
        model = DummyModel()
        machine = DummyModelStateMachine(model)
        fields = [transition.field for transition in machine.possible_transitions()]
        self.assertIn('publish', fields)

    def test_all_states_transition_from_any_non_target(self):
        machine = SimpleMachine()
        machine.state = 'draft'
        transition = BaseTransition(
            [AllStates()],
            PublishedState(),
            name='force',
            automatic=False,
        )
        transition.execute(machine)
        self.assertEqual(machine.state, 'published')

    def test_empty_state_singleton(self):
        self.assertIs(EmptyState(), EmptyState())
