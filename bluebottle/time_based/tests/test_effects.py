from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.effects.interests import DeleteInterestEffect
from bluebottle.time_based.models import DateRegistration
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateRegistrationFactory, InterestFactory
)


class DeleteInterestEffectTestCase(BluebottleTestCase):

    def test_condition_without_a_user(self):
        activity = DateActivityFactory.create()
        effect = DeleteInterestEffect(DateRegistration(activity=activity))

        self.assertFalse(effect.is_valid)

    def test_condition_with_a_matching_interest(self):
        registration = DateRegistrationFactory.create()
        InterestFactory.create(
            activity=registration.activity, user=registration.user, slot=None
        )
        effect = DeleteInterestEffect(registration)

        self.assertTrue(effect.is_valid)

    def test_condition_without_a_matching_interest(self):
        effect = DeleteInterestEffect(DateRegistrationFactory.create())

        self.assertFalse(effect.is_valid)
