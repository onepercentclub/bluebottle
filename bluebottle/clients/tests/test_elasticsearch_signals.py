from unittest.mock import patch

from bluebottle.activities.models import Activity
from bluebottle.clients.signals import TenantCelerySignalProcessor
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import DateActivityFactory


class TenantCelerySignalProcessorRegressionTestCase(BluebottleTestCase):
    """
    These tests intentionally capture current buggy behavior.

    In the buggy implementation, ES updates/deletes are skipped when the signal
    sender is the polymorphic parent model (Activity) and the registered
    document model is a child model (for example DateActivity).
    """

    def _processor(self):
        processor = TenantCelerySignalProcessor.__new__(TenantCelerySignalProcessor)
        processor.models = [DateActivity]
        processor.related_models = []
        return processor

    def test_save_is_skipped_for_parent_sender(self):
        processor = self._processor()
        activity = DateActivityFactory.create()

        with patch("bluebottle.clients.signals.registry_update_task.delay_on_commit") as delay_mock:
            processor.handle_save(Activity, activity)

        self.assertFalse(
            delay_mock.called,
            "Bug repro: save from parent sender should currently skip ES update task.",
        )

    def test_delete_is_skipped_for_parent_sender(self):
        processor = self._processor()
        activity = DateActivityFactory.create()

        with patch("bluebottle.clients.signals.registry.delete") as delete_mock:
            processor.handle_delete(Activity, activity)

        self.assertFalse(
            delete_mock.called,
            "Bug repro: delete from parent sender should currently skip ES delete.",
        )
