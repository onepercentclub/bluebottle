from django.test import TestCase

from bluebottle.fsm.triggers import ModelChangedTrigger, Trigger


class TriggerTestCase(TestCase):
    def test_model_changed_trigger_detects_field_change(self):
        trigger = ModelChangedTrigger(fields=['title'])
        instance = type('Instance', (), {
            '_initial_values': {'title': 'before'},
            'title': 'after',
        })()
        self.assertTrue(trigger.changed(instance))

    def test_model_changed_trigger_ignores_unchanged_field(self):
        trigger = ModelChangedTrigger(fields=['title'])
        instance = type('Instance', (), {
            '_initial_values': {'title': 'same'},
            'title': 'same',
        })()
        self.assertFalse(trigger.changed(instance))

    def test_trigger_execute_runs_effects_when_valid(self):
        executed = []

        class RecordingEffect(object):
            post_save = False
            conditions = []

            def __init__(self, instance, **kwargs):
                self.instance = instance

            @property
            def is_valid(self):
                return True

            def pre_save(self, **kwargs):
                executed.append(self)

            def __eq__(self, other):
                return type(self) is type(other)

        trigger = Trigger(effects=[RecordingEffect])
        instance = type('Instance', (), {'_postponed_effects': []})()
        trigger.execute(instance, [])
        self.assertEqual(len(executed), 1)
