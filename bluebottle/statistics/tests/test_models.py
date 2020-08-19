# coding=utf-8
import datetime
from django.utils import timezone
from django.test.utils import override_settings

from bluebottle.impact.tests.factories import (
    ImpactTypeFactory, ImpactGoalFactory
)
from bluebottle.statistics.tests.factories import (
    ManualStatisticFactory, DatabaseStatisticFactory, ImpactStatisticFactory
)
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class StatisticsModelTestCase(BluebottleTestCase):
    def setUp(self):
        super(StatisticsModelTestCase, self).setUp()

    def test_manual(self):
        stat = ManualStatisticFactory.create(name='Test', value=100)
        self.assertEqual(stat.get_value(), 100)

    def test_impact(self):
        type = ImpactTypeFactory()

        ImpactGoalFactory.create_batch(
            5,
            type=type,
            target=100,
            realized=50
        )

        stat = ImpactStatisticFactory.create(impact_type=type)

        self.assertEqual(stat.get_value(), 250.0)

    def test_impact_failed(self):
        type = ImpactTypeFactory()

        goals = ImpactGoalFactory.create_batch(
            5,
            type=type,
            target=100,
            realized=50
        )
        activity = goals[0].activity
        activity.status = 'failed'
        activity.save()

        stat = ImpactStatisticFactory.create(impact_type=type)

        self.assertEqual(stat.get_value(), 200.0)

    def test_database(self):
        initiative = InitiativeFactory.create()
        event = EventFactory.create(
            initiative=initiative,
            start=timezone.now() - datetime.timedelta(hours=1),
            duration=0.1

        )

        initiative.states.submit(save=True)
        initiative.states.approve(save=True)

        event.refresh_from_db()

        ParticipantFactory.create_batch(5, activity=event)

        stat = DatabaseStatisticFactory.create(name='Test', query='people_involved')

        self.assertEqual(stat.get_value(), 6)
