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
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activities.tasks import recommend, data_retention_contribution_task
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
            subscribed=True
        )
        self.user.place = PlaceFactory.create(
            position=self.amsterdam
        )

        for theme in ThemeFactory.create_batch(3):
            self.user.favourite_themes.add(theme)

        for skill in SkillFactory.create_batch(3):
            self.user.skills.add(skill)
        self.user.save()

        self.matches = []

        self.matches.append(
            PeriodActivityFactory.create(
                expertise=self.user.skills.first(),
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam),
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            )
        )

        self.matches.append(
            PeriodActivityFactory.create(
                expertise=None,
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam),
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            )
        )

        self.non_matches = []
        self.partial_matches = []

        # Wrong location, wrong theme, matching skill
        self.non_matches.append(
            PeriodActivityFactory.create(
                is_online=False,
                expertise=self.user.skills.first()
            )
        )
        # wrong skill, wrong theme, match location
        self.non_matches.append(
            PeriodActivityFactory.create(
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam)
            )
        )
        # wrong theme, matching location, matching skill
        self.partial_matches.append(
            PeriodActivityFactory.create(
                expertise=self.user.skills.first(),
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam)
            )
        )
        # wrong skill , matching location
        self.non_matches.append(
            PeriodActivityFactory.create(
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                ),
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam)
            )
        )
        # Wrong location
        self.non_matches.append(
            PeriodActivityFactory.create(
                is_online=False,
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                ),
                expertise=self.user.skills.first()
            )
        )

        # matching but applied
        activity = PeriodActivityFactory.create(
            expertise=self.user.skills.first(),
            is_online=False,
            location=GeolocationFactory.create(position=self.close_to_amsterdam),
            initiative=InitiativeFactory.create(
                theme=self.user.favourite_themes.first()
            )
        )
        PeriodParticipantFactory.create(activity=activity, user=self.user)
        self.non_matches.append(activity)

        for activity in self.matches + self.non_matches + self.partial_matches:
            activity.initiative.states.submit(save=True)
            activity.initiative.states.approve(save=True)

        # matching but incorrect status
        self.non_matches.append(
            PeriodActivityFactory.create(
                expertise=self.user.skills.first(),
                is_online=False,
                location=GeolocationFactory.create(position=self.close_to_amsterdam),
                initiative=InitiativeFactory.create(
                    theme=self.user.favourite_themes.first()
                )
            )
        )

        mail.outbox = []

    def test_including_partial(self):
        recommend()
        body = mail.outbox[-1].body
        self.assertEqual(
            mail.outbox[-1].subject,
            '{}, there are 3 activities on Test matching your profile'.format(
                self.user.first_name
            )
        )

        self.assertTrue('/en/initiatives/activities/list' in body)
        self.assertTrue(
            'There are tons of cool activities on Test that are making a positive impact.'
            in body
        )

        self.assertTrue(
            'We have selected 3 activities that match with your profile. Join us!'
            in body
        )
        self.assertFalse(
            "Complete your profile, so that we can select even more relevant activities for you"
            in body
        )

        for activity in self.matches + self.partial_matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

        for activity in self.non_matches:
            self.assertFalse(activity.title in body)
            self.assertFalse(activity.get_absolute_url() in body)

    def test_no_user_skill(self):
        self.user.skills.clear()

        recommend()
        body = mail.outbox[-1].body

        self.assertTrue('/en/initiatives/activities/list' in body)
        self.assertTrue(
            (
                "[ Complete your profile ](https://testserver/member/profile) , "
                "so that we can select even more relevant activities for you"
            ) in body
        )

        for activity in self.matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

        for activity in self.non_matches:
            activity.refresh_from_db()
            if (
                activity.location.position == self.close_to_amsterdam and
                activity.initiative.theme in self.user.favourite_themes.all() and
                activity.status == 'open' and
                not len(activity.participants.all())
            ):
                self.assertTrue(activity.title in body)
                self.assertTrue(activity.get_absolute_url() in body)

            else:
                self.assertFalse(activity.title in body)
                self.assertFalse(activity.get_absolute_url() in body)

    def test_including_partial_location(self):
        self.user.place = None
        self.user.location = LocationFactory.create(position=self.amsterdam)
        self.user.save()

        recommend()
        body = mail.outbox[-1].body

        self.assertTrue('/en/initiatives/activities/list' in body)
        self.assertFalse(
            "Complete your profile, so that we can select even more relevant activities for you"
            in body
        )

        for activity in self.matches + self.partial_matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

        for activity in self.non_matches:
            self.assertFalse(activity.title in body)
            self.assertFalse(activity.get_absolute_url() in body)

    def test_not_including_partial(self):
        activity = PeriodActivityFactory.create(
            expertise=self.user.skills.first(),
            is_online=False,
            location=GeolocationFactory.create(position=self.close_to_amsterdam),
            initiative=InitiativeFactory.create(
                theme=self.user.favourite_themes.first()
            )
        )
        activity.initiative.states.submit(save=True)
        activity.initiative.states.approve(save=True)
        self.matches.append(activity)

        recommend()
        body = mail.outbox[-1].body

        self.assertTrue('/en/initiatives/activities/list' in body)

        for activity in self.matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

        for activity in self.non_matches + self.partial_matches:
            self.assertFalse(activity.title in body)
            self.assertFalse(activity.get_absolute_url() in body)

    def test_not_including_closed_segment(self):
        closed_segment = SegmentFactory.create(closed=True)
        activity = self.matches.pop()
        activity.segments.set([closed_segment])

        for act in self.partial_matches:
            act.delete()

        recommend()

        body = mail.outbox[-1].body

        self.assertEqual(
            mail.outbox[-1].subject,
            '{}, there are 1 activities on Test matching your profile'.format(
                self.user.first_name
            )
        )

        self.assertTrue('/en/initiatives/activities/list' in body)

        self.assertFalse(activity.title in body)
        self.assertFalse(activity.get_absolute_url() in body)

        for activity in self.matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

    def test_including_closed_segment(self):
        closed_segment = SegmentFactory.create(closed=True)
        activity = self.matches.pop()
        activity.segments.set([closed_segment])

        self.user.segments.set([closed_segment])

        for act in self.partial_matches:
            act.delete()

        recommend()

        body = mail.outbox[-1].body

        self.assertEqual(
            mail.outbox[-1].subject,
            '{}, there are 2 activities on Test matching your profile'.format(
                self.user.first_name
            )
        )

        self.assertTrue('/en/initiatives/activities/list' in body)

        self.assertTrue(activity.title in body)
        self.assertTrue(activity.get_absolute_url() in body)

        for activity in self.matches:
            self.assertTrue(activity.title in body)
            self.assertTrue(activity.get_absolute_url() in body)

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
