from bluebottle.follow.models import Follow, follow
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class FollowTestCase(BluebottleTestCase):

    def test_survive_and_fix_duplicate_follows(self):
        user = BlueBottleUserFactory.create()
        funding = FundingFactory.create()
        Follow.objects.create(
            instance=funding,
            user=user
        )
        Follow.objects.create(
            instance=funding,
            user=user
        )
        follow(user, funding)
        self.assertEqual(Follow.objects.count(), 1)
