from django.test import TestCase

from bluebottle.activities.models import Activity
from bluebottle.deeds.models import Deed
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory, OrganizationMemberFactory
from bluebottle.time_based.tests.factories import DeadlineActivityFactory


class ActivityModelTestCase(TestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()

        for category in CategoryFactory.create_batch(3):
            self.initiative.categories.add(category)

    def test_categories(self):
        deed = Deed.objects.create(initiative=self.initiative)
        self.assertEqual(
            len(deed.categories.all()),
            3
        )

    def test_categories_no_initiatve(self):
        deed = Deed.objects.create(owner=BlueBottleUserFactory.create())
        self.assertEqual(
            len(deed.categories.all()),
            0
        )


class ActivityOrganizationTestCase(TestCase):
    def setUp(self):
        self.membership = OrganizationMemberFactory.create()
        self.member = self.membership.member

    def test_member_organization(self):
        deed = DeedFactory.create(owner=self.member)
        self.assertEqual(deed.organization, self.membership.organization)

    def test_member_organization_deadline(self):
        activity = DeadlineActivityFactory.create(owner=self.member)
        self.assertEqual(activity.organization, self.membership.organization)

    def test_member_organization_takes_precedence_over_initiative(self):
        initiative = InitiativeFactory.create(
            has_organization=True, organization=OrganizationFactory.create()
        )
        deed = DeedFactory.create(initiative=initiative, owner=self.member)
        self.assertEqual(deed.organization, self.membership.organization)

    def test_no_membership(self):
        initiative = InitiativeFactory.create(
            has_organization=True, organization=OrganizationFactory.create()
        )
        deed = DeedFactory.create(initiative=initiative)
        self.assertIsNone(deed.organization)

    def test_keeps_explicit_organization(self):
        other = OrganizationFactory.create()
        deed = DeedFactory.create(owner=self.member, organization=other)
        self.assertEqual(deed.organization, other)

    def test_existing_activity_not_linked(self):
        member = BlueBottleUserFactory.create()
        deed = DeedFactory.create(owner=member)
        OrganizationMemberFactory.create(member=member)
        deed.title = 'Changed'
        deed.save()
        deed.refresh_from_db()
        self.assertIsNone(deed.organization)

    def test_cleared_organization_not_refilled(self):
        deed = DeedFactory.create(owner=self.member)
        deed.organization = None
        deed.save()
        deed.refresh_from_db()
        self.assertIsNone(deed.organization)

    def test_does_not_create_membership(self):
        organization = OrganizationFactory.create()
        DeedFactory.create(organization=organization)
        self.assertEqual(organization.members.count(), 0)


class ActivitySegmentsTestCase(TestCase):
    def setUp(self):
        team_type = SegmentTypeFactory.create(name='Team')
        self.team = SegmentFactory.create(name='Online Marketing', segment_type=team_type)
        self.other_team = SegmentFactory.create(name='Direct Marketing', segment_type=team_type)

        unit_type = SegmentTypeFactory.create(name='Unit')
        self.unit = SegmentFactory.create(name='Marketing', segment_type=unit_type)
        SegmentFactory.create(name='Communications', segment_type=unit_type)

        self.user = BlueBottleUserFactory()
        self.user.segments.add(self.team)
        self.user.segments.add(self.unit)

        super(ActivitySegmentsTestCase, self).setUp()

    def test_segments(self):
        activity = DeadlineActivityFactory.create(owner=self.user)
        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.team in activity.segments.all())

    def test_segments_already_set(self):
        activity = DeadlineActivityFactory.create(owner=self.user, status='succeeded')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.team in activity.segments.all())
        self.assertFalse(self.other_team in activity.segments.all())

    def test_segments_already_set_open(self):
        activity = DeadlineActivityFactory.create(owner=self.user, status='open')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.other_team in activity.segments.all())
        self.assertFalse(self.team in activity.segments.all())

    def test_segments_already_set_draft(self):
        activity = DeadlineActivityFactory.create(owner=self.user, status='draft')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.other_team in activity.segments.all())
        self.assertFalse(self.team in activity.segments.all())

    def test_delete_segment(self):
        activity = DeadlineActivityFactory.create(owner=self.user)

        self.team.delete()

        self.assertTrue(self.unit in activity.segments.all())
        self.assertFalse(self.team in activity.segments.all())

    def test_office_location_required(self):
        LocationFactory.create_batch(3)
        activity = DeadlineActivityFactory.create()
        self.assertTrue('office_location' in activity.required_fields)

    def test_office_location_not_required(self):
        activity = DeadlineActivityFactory.create()
        self.assertFalse('office_location' in activity.required_fields)


class ActivitySlugTestCase(TestCase):

    def test_long_title_produces_a_slug_that_fits(self):
        max_length = Activity._meta.get_field('slug').max_length
        activity = DeedFactory.create(title='a' * 255, slug='new')

        self.assertLessEqual(len(activity.slug), max_length)
        self.assertTrue(activity.slug.startswith('aaa'))

    def test_transliterated_title_produces_a_slug_that_fits(self):
        max_length = Activity._meta.get_field('slug').max_length
        activity = DeedFactory.create(title='ä' * 200, slug='new')

        self.assertLessEqual(len(activity.slug), max_length)

    def test_empty_title_still_falls_back_to_new(self):
        activity = DeedFactory.create(title='', slug='new')

        self.assertEqual(activity.slug, 'new')

    def test_short_title_is_not_truncated(self):
        activity = DeedFactory.create(title='A normal title', slug='new')

        self.assertEqual(activity.slug, 'a-normal-title')

    def test_truncated_slug_has_no_trailing_hyphen(self):
        activity = DeedFactory.create(title='word ' * 40, slug='new')

        self.assertLessEqual(
            len(activity.slug), Activity._meta.get_field('slug').max_length
        )
        self.assertFalse(activity.slug.endswith('-'))

    def test_two_long_titles_sharing_a_prefix_both_save(self):
        """slug is indexed but not unique, so truncation needs no suffix."""
        prefix = 'a' * 120
        first = DeedFactory.create(title=prefix + ' one', slug='new')
        second = DeedFactory.create(title=prefix + ' two', slug='new')

        self.assertEqual(first.slug, second.slug)
        self.assertNotEqual(first.pk, second.pk)
