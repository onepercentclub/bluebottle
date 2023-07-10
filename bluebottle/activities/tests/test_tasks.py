from bluebottle.members.models import MemberPlatformSettings
from dateutil.relativedelta import relativedelta
from django.test.utils import override_settings
from django.test import tag
from django.contrib.gis.geos import Point
from django.core import mail
from django.utils.timezone import now

from django_elasticsearch_dsl.test import ESTestCase

from bluebottle.activities.models import Contributor
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.offices.tests.factories import OfficeSubRegionFactory, OfficeRegionFactory
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activities.tasks import (
    recommend, get_matching_activities, data_retention_contribution_task
)
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, PeriodParticipantFactory, SkillFactory, DateActivityFactory, DateParticipantFactory
)
from bluebottle.test.factory_models.geo import LocationFactory, PlaceFactory, GeolocationFactory

from bluebottle.test.factory_models.projects import ThemeFactory


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class RecommendTaskTestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(enable_matching_emails=True)

        self.amsterdam = Point(x=4.8981734, y=52.3790565)
        self.close_to_amsterdam = Point(x=4.9848386, y=52.3929661)
        self.rotterdam = Point(x=4.4207882, y=51.9280712)

        self.user = BlueBottleUserFactory.create(
            subscribed=True,
            search_distance=50,
            any_search_distance=False,
            exclude_online=False
        )
        self.user.place = PlaceFactory.create(
            position=self.amsterdam
        )

        for theme in ThemeFactory.create_batch(3):
            self.user.favourite_themes.add(theme)

        for skill in SkillFactory.create_batch(3):
            self.user.skills.add(skill)

        self.user.save()

        self.matching = [
            # Online
            PeriodActivityFactory.create(
                status="open",
                is_online=True,
                location=None,
            ),

            # Matching skill, matching place
            PeriodActivityFactory.create(
                status="open",
                expertise=self.user.skills.first(),
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam)
            ),

            # Matching theme, online
            PeriodActivityFactory.create(
                status="open",
                location=None,
                is_online=True,
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            ),

            # Matching place, theme and no skill
            PeriodActivityFactory.create(
                status="open",
                expertise=None,
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam),
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            ),

            # Matching theme, skill, online
            PeriodActivityFactory.create(
                status="open",
                expertise=self.user.skills.first(),
                location=None,
                is_online=True,
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            ),

            # Matching place, theme and skill
            PeriodActivityFactory.create(
                status="open",
                is_online=False,
                expertise=self.user.skills.first(),
                location=GeolocationFactory.create(position=self.close_to_amsterdam),
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            ),

        ]

    def test_recommend(self):
        recommend()
        self.assertEqual(len(mail.outbox), 1)

    def test_recommend_no_matching(self):
        for activity in self.matching:
            activity.delete()

        recommend()
        self.assertEqual(len(mail.outbox), 0)

    def test_include_matching(self):
        activities = get_matching_activities(self.user)

        self.assertEqual(
            set(activity.pk for activity in activities),
            set(match.pk for match in self.matching)
        )

    def test_order_matching(self):
        activities = get_matching_activities(self.user)
        self.assertEqual(
            [activity.pk for activity in activities],
            list(reversed([match.pk for match in self.matching]))
        )

    def test_not_including_closed_segment(self):
        closed_segment = SegmentFactory.create(closed=True)
        activity = self.matching[-1]
        activity.segments.set([closed_segment])

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_including_closed_segment(self):
        closed_segment = SegmentFactory.create(closed=True)
        activity = self.matching[-1]
        activity.segments.set([closed_segment])

        self.user.segments.set([closed_segment])

        activities = get_matching_activities(self.user)
        self.assertTrue(activity in activities)

    def test_exlcude_office(self):
        activity = self.matching[-1]
        activity.office_location = LocationFactory.create()
        activity.office_restriction = 'office'
        activity.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_exclude_office_no_office(self):
        activity = self.matching[-1]

        activity.office_restriction = 'office'
        activity.office_location = LocationFactory.create()
        activity.save()

        self.user.location = LocationFactory.create()
        self.user.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_include_office(self):
        activity = self.matching[-1]

        activity.office_location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create()
        )
        activity.office_restriction = 'office'
        activity.save()

        self.user.location = activity.office_location
        self.user.save()

        activities = get_matching_activities(self.user)
        self.assertTrue(activity in activities)

    def test_exlcude_office_sub_region(self):
        activity = self.matching[-1]

        activity.office_location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create()
        )
        activity.office_restriction = 'office_subregion'
        activity.save()

        activities = get_matching_activities(self.user)

        self.assertFalse(activity in activities)

    def test_include_office_sub_region(self):
        activity = self.matching[-1]

        activity.office_location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create()
        )

        activity.office_restriction = 'office_subregion'
        activity.save()

        self.user.location = LocationFactory.create(
            subregion=activity.office_location.subregion
        )
        self.user.save()

        activities = get_matching_activities(self.user)
        self.assertTrue(activity in activities)

    def test_exlcude_office_region(self):
        activity = self.matching[-1]
        activity.office_location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create(
                region=OfficeRegionFactory.create()
            )
        )
        activity.office_restriction = 'office_region'
        activity.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_include_office_region(self):
        activity = self.matching[-1]

        activity.office_location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create(
                region=OfficeRegionFactory.create()
            )
        )
        activity.office_restriction = 'office_region'
        activity.save()

        self.user.location = LocationFactory.create(
            subregion=OfficeSubRegionFactory.create(
                region=activity.office_location.subregion.region
            )
        )
        self.user.save()

        activities = get_matching_activities(self.user)
        self.assertTrue(activity in activities)

    def test_exclude_contributed_to(self):
        activity = self.matching[-1]
        PeriodParticipantFactory.create(activity=activity, user=self.user)

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_exclude_distance(self):
        activity = self.matching[-1]
        activity.location = GeolocationFactory.create(position=self.rotterdam)
        activity.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_exclude_draft(self):
        activity = self.matching[-1]
        activity.status = 'draft'
        activity.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_exclude_succeeded(self):
        activity = self.matching[-1]
        activity.status = 'succeeded'
        activity.save()

        activities = get_matching_activities(self.user)
        self.assertFalse(activity in activities)

    def test_exclude_online(self):
        self.user.exclude_online = True
        self.user.save()

        activities = get_matching_activities(self.user)
        for activity in activities:
            self.assertTrue(activity.is_online)

    def test_not_subscribed(self):
        self.user.subscribed = False
        self.user.save()

        recommend()

        self.assertEqual(len(mail.outbox), 0)

    def test_not_enabled(self):
        self.settings.enable_matching_emails = False
        self.settings.save()

        recommend()

        self.assertEqual(len(mail.outbox), 0)


class ContributorDataRetentionTest(BluebottleTestCase):

    def create_contributors(self, factory, activity, dates):
        for date in dates:
            contributor = factory.create(activity=activity)
            contributor.created = date
            contributor.save()
            contributor.contributions.update(status='succeeded')

    def setUp(self):
        super(ContributorDataRetentionTest, self).setUp()
        months_ago_12 = now() - relativedelta(months=12)
        months_ago_8 = now() - relativedelta(months=8)
        months_ago_2 = now() - relativedelta(months=2)

        self.activity1 = DateActivityFactory.create()
        self.activity2 = PeriodActivityFactory.create()
        self.activity3 = DeedFactory.create()

        self.create_contributors(DateParticipantFactory, self.activity1, [months_ago_12, months_ago_8])
        self.create_contributors(PeriodParticipantFactory, self.activity2, [months_ago_12, months_ago_2])
        self.create_contributors(DeedParticipantFactory, self.activity3, [months_ago_8, months_ago_2])

        self.task = data_retention_contribution_task

    def test_data_retention_dont_delete_without_settings(self):
        self.assertEqual(Contributor.objects.count(), 9)
        self.task()
        self.assertEqual(Contributor.objects.count(), 9)

    def test_data_retention_clean_up(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.retention_delete = 10
        member_settings.retention_anonymize = 6
        member_settings.save()
        self.task()
        self.assertEqual(Contributor.objects.count(), 7)
        self.assertEqual(Contributor.objects.filter(user__isnull=True).count(), 2)
        self.activity1.refresh_from_db()
        self.assertEqual(self.activity1.deleted_successful_contributors, 1)
        self.activity2.refresh_from_db()
        self.assertEqual(self.activity2.deleted_successful_contributors, 1)
