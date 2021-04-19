from django.test.utils import override_settings
from django.test import tag
from django.contrib.gis.geos import Point
from django.core import mail

from django_elasticsearch_dsl.test import ESTestCase


from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activities.tasks import recommend
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, PeriodParticipantFactory
)
from bluebottle.test.factory_models.geo import LocationFactory, PlaceFactory, GeolocationFactory

from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.factory_models.tasks import SkillFactory


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
        PlaceFactory.create(
            content_object=self.user,
            position=self.amsterdam
        )

        for theme in ThemeFactory.create_batch(3):
            self.user.favourite_themes.add(theme)

        for skill in SkillFactory.create_batch(3):
            self.user.skills.add(skill)

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

        self.matches.append(
            PeriodActivityFactory.create(
                expertise=self.user.skills.first(),
                is_online=True,
                location=GeolocationFactory.create(position=self.rotterdam),
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

    def test_no_user_skill(self):
        self.user.skills.clear()

        recommend()
        body = mail.outbox[-1].body

        self.assertTrue('/en/initiatives/activities/list' in body)
        self.assertTrue(
            "Complete your profile, so that we can select even more relevant activities for you"
            in body
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
        self.user.place.delete()
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
