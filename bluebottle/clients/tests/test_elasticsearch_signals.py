from unittest.mock import MagicMock, patch

from django.db import connection

from bluebottle.activities.models import Activity
from bluebottle.clients.signals import (
    TenantCelerySignalProcessor,
    registry_delete_related_task,
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
)


class TenantCelerySignalProcessorRegressionTestCase(BluebottleTestCase):
    """
    Regression tests ES updates/deletes are no longer skipped when the signal
    sender is the polymorphic parent model (Activity) and the registered
    document model is a child model (for example DateActivity).
    """

    def _processor(self):
        processor = TenantCelerySignalProcessor.__new__(TenantCelerySignalProcessor)
        processor.models = [DateActivity]
        processor.related_models = []
        return processor

    def test_save_is_not_skipped_for_parent_sender(self):
        processor = self._processor()
        activity = DateActivityFactory.create()

        with patch("bluebottle.clients.signals.registry_update_task.delay_on_commit") as delay_mock:
            processor.handle_save(Activity, activity)

        self.assertTrue(
            delay_mock.called,
            "save from parent sender should not skip ES update task.",
        )
        model_info = delay_mock.call_args.args[0]
        self.assertEqual(model_info["model_name"], "dateactivity")

    def test_delete_is_not_skipped_for_parent_sender(self):
        processor = self._processor()
        activity = DateActivityFactory.create()

        with patch("bluebottle.clients.signals.registry.delete") as delete_mock:
            processor.handle_delete(Activity, activity)

        self.assertTrue(
            delete_mock.called,
            "delete from parent sender should not skip ES delete.",
        )
        self.assertEqual(delete_mock.call_args.kwargs.get("raise_on_error"), False)


class RelatedDeleteReindexRaceTestCase(BluebottleTestCase):
    """
    When a DateActivity is hard-deleted, slots cascade-delete first.

    Slot pre_delete schedules registry_delete_related_task with the parent
    activity. Activity post_delete sync-removes it from ES. After commit the
    related task must not re-index that stale in-memory parent (default
    Document.update action is 'index').
    """

    def _assert_update_is_delete_action(self, update_mock):
        self.assertTrue(update_mock.called, "expected an ES update call")
        for call in update_mock.call_args_list:
            _args, kwargs = call
            self.assertEqual(
                kwargs.get("action"),
                "delete",
                "related delete task must not re-index a parent that no longer exists "
                f"(got kwargs={kwargs!r})",
            )
            self.assertEqual(
                kwargs.get("raise_on_error"),
                False,
                "duplicate ES deletes after sync handle_delete must not raise",
            )

    def test_related_delete_task_does_not_reindex_deleted_parent(self):
        activity = DateActivityFactory.create()
        stale_activity = activity
        activity_id = activity.pk

        # Parent is already gone when the deferred related task runs.
        DateActivity.objects.filter(pk=activity_id).delete()
        self.assertFalse(DateActivity.objects.filter(pk=activity_id).exists())

        doc_instance = MagicMock()
        registry_delete_related_task(doc_instance, stale_activity, connection.tenant)

        self._assert_update_is_delete_action(doc_instance.update)

    def test_related_delete_task_still_reindexes_existing_parent(self):
        """Deleting only a related child should still refresh the parent in ES."""
        activity = DateActivityFactory.create()
        doc_instance = MagicMock()

        registry_delete_related_task(doc_instance, activity, connection.tenant)

        self.assertTrue(doc_instance.update.called)
        _args, kwargs = doc_instance.update.call_args
        self.assertNotEqual(
            kwargs.get("action"),
            "delete",
            "existing parents should keep being re-indexed after related deletes",
        )
        self.assertEqual(_args[0], activity)

    def test_slot_pre_delete_related_task_does_not_reindex_cascaded_parent(self):
        """
        End-to-end signal/task race for cascade delete:

        1. slot pre_delete schedules related task with parent activity
        2. parent is removed from DB (and would be sync-deleted from ES)
        3. deferred task runs and must not put the parent back
        """
        activity = DateActivityFactory.create()
        slot = activity.slots.first() or DateActivitySlotFactory.create(activity=activity)
        processor = TenantCelerySignalProcessor.__new__(TenantCelerySignalProcessor)

        scheduled = []

        def capture_delay(doc_instance, related, tenant):
            scheduled.append((doc_instance, related, tenant))

        with patch(
            "bluebottle.clients.signals.registry_delete_related_task.delay_on_commit",
            side_effect=capture_delay,
        ):
            processor.handle_pre_delete(slot.__class__, slot)

        self.assertTrue(scheduled, "slot pre_delete should schedule a related ES task")
        for _doc_instance, related, _tenant in scheduled:
            # Related parents must be materialized before commit.
            self.assertFalse(hasattr(related, "query"))

        # Simulate activity cascade delete completing before on_commit tasks run.
        activity_id = activity.pk
        DateActivity.objects.filter(pk=activity_id).delete()
        self.assertFalse(DateActivity.objects.filter(pk=activity_id).exists())

        for doc_instance, related, tenant in scheduled:
            # Replace doc with a mock so we can assert the update action without ES.
            mock_doc = MagicMock()
            registry_delete_related_task(mock_doc, related, tenant)
            self._assert_update_is_delete_action(mock_doc.update)

    def test_pre_delete_materializes_queryset_related_parents(self):
        activity = DateActivityFactory.create()
        # Participant-style related lookups return querysets; materialize before deferral.
        related_qs = DateActivity.objects.filter(pk=activity.pk)
        processor = TenantCelerySignalProcessor.__new__(TenantCelerySignalProcessor)

        scheduled = []

        def capture_delay(doc_instance, related, tenant):
            scheduled.append(related)

        fake_doc = MagicMock()
        fake_doc.return_value.get_instances_from_related.return_value = related_qs

        with patch(
            "bluebottle.clients.signals.registry._get_related_doc",
            return_value=[fake_doc],
        ), patch(
            "bluebottle.clients.signals.registry_delete_related_task.delay_on_commit",
            side_effect=lambda doc_instance, related, tenant: capture_delay(
                doc_instance, related, tenant
            ),
        ):
            processor.handle_pre_delete(DateActivity, activity)

        self.assertEqual(len(scheduled), 1)
        self.assertIsInstance(scheduled[0], list)
        self.assertEqual(scheduled[0][0].pk, activity.pk)
