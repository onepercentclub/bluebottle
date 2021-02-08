from django.core import mail

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class InitiativeTriggerTests(BluebottleTestCase):
    def setUp(self):
        super(InitiativeTriggerTests, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='Bart', last_name='Lacroix')
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            organization=None
        )

    def test_set_reviewer(self):
        mail.outbox = []
        self.initiative.reviewer = BlueBottleUserFactory.create(email='reviewer@goodup.com')
        self.initiative.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('You are assigned as reviewer' in mail.outbox[0].body)
        self.assertEqual(['reviewer@goodup.com'], mail.outbox[0].to)
