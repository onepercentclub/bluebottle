from unittest import mock

from django.test import TestCase

from bluebottle.fsm.effects import Effect, TransitionEffect
from bluebottle.fsm.state import TransitionNotPossible


class EffectTestCase(TestCase):
    def test_effect_is_valid_when_conditions_pass(self):
        instance = object()

        class AlwaysValidEffect(Effect):
            conditions = [lambda effect: True]

        self.assertTrue(AlwaysValidEffect(instance).is_valid)

    def test_effect_is_invalid_when_condition_fails(self):
        instance = object()

        class FailingEffect(Effect):
            conditions = [lambda effect: False]

        self.assertFalse(FailingEffect(instance).is_valid)

    def test_transition_effect_executes_transition(self):
        transition = mock.Mock()
        transition.target.name = 'open'
        machine = mock.Mock()
        machine.possible_transitions.return_value = [transition]

        instance = mock.Mock()
        instance.states = machine

        effect = TransitionEffect(transition)(instance)
        effect.pre_save()
        transition.execute.assert_called_once_with(machine)

    def test_transition_effect_swallows_transition_not_possible(self):
        transition = mock.Mock()
        transition.execute.side_effect = TransitionNotPossible()
        machine = mock.Mock()
        machine.possible_transitions.return_value = [transition]

        instance = mock.Mock()
        instance.states = machine

        effect = TransitionEffect(transition)(instance)
        effect.pre_save()
        transition.execute.assert_called_once_with(machine)
