from django.test import TestCase

from bluebottle.activity_pub.tests.factories import GoodDeedFactory
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory

from bluebottle.cms.models import SitePlatformSettings


class DeedModelTestCase(TestCase):
    def setUp(self):

        self.model = DeedFactory.create(target=None)

        super(DeedModelTestCase, self).setUp()

    def test_required(self):
        self.assertEqual(list(self.model.required), [])

    def test_required_with_impact(self):
        self.model.enable_impact = True
        self.model.save()

        self.assertEqual(list(self.model.required), ['goals', 'target'])

    def test_required_with_impact_target_and_goal(self):
        self.model.enable_impact = True
        self.model.target = 100
        self.model.save()

        ImpactGoalFactory.create(activity=self.model)

        self.assertEqual(list(self.model.required), [])

    def test_readonly_fields(self):
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        GoodDeedFactory.create(
            adopted=self.model
        )

        self.assertEqual(
            self.model.readonly_fields,
            [
                'title',
                'description',
                'image',
                'video_url',
                'slug',
                'next_step_link',
                'next_step_title',
                'next_step_button_label',
                'next_step_description',
                'start',
                'end',
                'target'
            ]
        )
