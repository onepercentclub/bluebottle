from bluebottle.activities.documents import ActivityDocument
from bluebottle.activities.models import Activity, Contributor, Organizer
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import Registration
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    InterestFactory,
)


class ActivityDocumentContributorTestCase(BluebottleTestCase):
    def set_status(self, contributors, status):
        Contributor.objects.filter(pk__in=[c.pk for c in contributors]).update(status=status)

    def add_organizer(self, activity):
        Organizer.objects.create(activity=activity, user=activity.owner, status='succeeded')

    def prepare(self, activity):
        activity = Activity.objects.get(pk=activity.pk)
        document = ActivityDocument()
        return (
            document.prepare_contributor_count(activity),
            document.prepare_contributor_stats(activity),
            document.prepare_registration_stats(activity),
        )

    def test_deadline_activity(self):
        activity = DeadlineActivityFactory.create()
        self.add_organizer(activity)
        participants = DeadlineParticipantFactory.create_batch(5, activity=activity)
        self.set_status(participants[:2], 'accepted')
        self.set_status(participants[2:3], 'succeeded')
        self.set_status(participants[3:4], 'new')
        self.set_status(participants[4:], 'withdrawn')
        Activity.objects.filter(pk=activity.pk).update(deleted_successful_contributors=2)
        InterestFactory.create_batch(2, activity=activity)

        registration_ids = list(Registration.objects.filter(activity=activity).values_list('pk', flat=True))
        Registration.objects.filter(pk__in=registration_ids[:1]).update(status='new')
        Registration.objects.filter(pk__in=registration_ids[1:]).update(status='accepted')

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(count, 2 + 1 + 2)
        self.assertEqual(contributors['accepted'], 2)
        self.assertEqual(contributors['succeeded'], 3)
        self.assertEqual(contributors['interested'], 2)
        self.assertEqual(registrations['pending'], 1)
        self.assertEqual(registrations['accepted'], len(registration_ids) - 1)

    def test_interested_counts_people_once(self):
        activity = DateActivityFactory.create()
        slots = [activity.slots.first(), DateActivitySlotFactory.create(activity=activity)]
        user = BlueBottleUserFactory.create()
        for slot in slots:
            InterestFactory.create(activity=activity, slot=slot, user=user)
        InterestFactory.create(activity=activity, slot=slots[0])

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(contributors['interested'], 2)

    def test_interested_excludes_participants(self):
        activity = DeadlineActivityFactory.create()
        joined, withdrawn = DeadlineParticipantFactory.create_batch(2, activity=activity)
        self.set_status([withdrawn], 'withdrawn')
        for participant in (joined, withdrawn):
            InterestFactory.create(activity=activity, user=participant.user)
        InterestFactory.create(activity=activity)

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(contributors['interested'], 2)

    def test_deed_excludes_organizer(self):
        activity = DeedFactory.create()
        self.add_organizer(activity)
        participants = DeedParticipantFactory.create_batch(3, activity=activity)
        self.set_status(participants[:1], 'accepted')
        self.set_status(participants[1:], 'succeeded')

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(count, 3)
        self.assertEqual(contributors['succeeded'], 2)
        self.assertEqual(registrations['pending'], 0)

    def test_funding_counts_succeeded_donors(self):
        activity = FundingFactory.create()
        self.add_organizer(activity)
        donors = DonorFactory.create_batch(4, activity=activity)
        self.set_status(donors[:2], 'succeeded')
        self.set_status(donors[2:3], 'failed')
        self.set_status(donors[3:], 'refunded')

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(count, 2)
        self.assertEqual(contributors['succeeded'], 2)

    def test_without_contributors(self):
        activity = DeedFactory.create()

        count, contributors, registrations = self.prepare(activity)

        self.assertEqual(count, 0)
        self.assertFalse(any(contributors.values()))
        self.assertFalse(any(registrations.values()))
        self.assertEqual(set(contributors), {'accepted', 'scheduled', 'succeeded', 'interested'})
        self.assertEqual(set(registrations), {'pending', 'accepted'})
