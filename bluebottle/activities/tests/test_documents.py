from bluebottle.activities.documents import ActivityDocument
from bluebottle.activities.models import Activity, Contributor, Organizer
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import Registration
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
)


class ActivityDocumentContributorTestCase(BluebottleTestCase):
    def set_status(self, contributors, status):
        Contributor.objects.filter(pk__in=[c.pk for c in contributors]).update(status=status)

    def add_organizer(self, activity):
        Organizer.objects.create(activity=activity, user=activity.owner, status='succeeded')

    def prepare(self, activity):
        activity = Activity.objects.get(pk=activity.pk)
        document = ActivityDocument()
        return document.prepare_contributor_count(activity), document.prepare_contributor_stats(activity)

    def test_deadline_activity(self):
        activity = DeadlineActivityFactory.create()
        self.add_organizer(activity)
        participants = DeadlineParticipantFactory.create_batch(5, activity=activity)
        self.set_status(participants[:2], 'accepted')
        self.set_status(participants[2:3], 'succeeded')
        self.set_status(participants[3:4], 'new')
        self.set_status(participants[4:], 'withdrawn')
        Activity.objects.filter(pk=activity.pk).update(deleted_successful_contributors=2)

        registrations = Registration.objects.filter(activity=activity)
        Registration.objects.filter(pk__in=[r.pk for r in registrations[:1]]).update(status='new')
        Registration.objects.filter(pk__in=[r.pk for r in registrations[1:]]).update(status='accepted')

        count, stats = self.prepare(activity)

        self.assertEqual(count, 2 + 1 + 2)
        self.assertEqual(stats['participants']['accepted'], 2)
        self.assertEqual(stats['participants']['succeeded'], 3)
        self.assertEqual(stats['participants']['new'], 1)
        self.assertEqual(stats['participants']['withdrawn'], 1)
        self.assertEqual(stats['participants']['rejected'], 0)
        self.assertEqual(stats['registrations']['to_review'], 1)
        self.assertEqual(stats['registrations']['accepted'], registrations.count() - 1)

    def test_deed_excludes_organizer(self):
        activity = DeedFactory.create()
        self.add_organizer(activity)
        participants = DeedParticipantFactory.create_batch(3, activity=activity)
        self.set_status(participants[:1], 'accepted')
        self.set_status(participants[1:], 'succeeded')

        count, stats = self.prepare(activity)

        self.assertEqual(count, 3)
        self.assertEqual(stats['participants']['succeeded'], 2)
        self.assertEqual(stats['registrations']['to_review'], 0)

    def test_funding_counts_succeeded_donors(self):
        activity = FundingFactory.create()
        self.add_organizer(activity)
        donors = DonorFactory.create_batch(4, activity=activity)
        self.set_status(donors[:2], 'succeeded')
        self.set_status(donors[2:3], 'failed')
        self.set_status(donors[3:], 'refunded')

        count, stats = self.prepare(activity)

        self.assertEqual(count, 2)
        self.assertEqual(stats['participants']['succeeded'], 2)
        self.assertEqual(stats['participants']['failed'], 1)
        self.assertEqual(stats['participants']['refunded'], 1)

    def test_without_contributors(self):
        activity = DeedFactory.create()

        count, stats = self.prepare(activity)

        self.assertEqual(count, 0)
        self.assertEqual(set(stats), {'participants', 'registrations'})
        self.assertFalse(any(stats['participants'].values()))
        self.assertFalse(any(stats['registrations'].values()))
