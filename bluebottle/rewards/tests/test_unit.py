from bluebottle.donations.models import Donation
from bluebottle.rewards.models import Reward
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.utils import BluebottleTestCase


class RewardTestCase(BluebottleTestCase):
    """
    Test Rewards
    """

    def test_delete_reward(self):
        """
        Deleting rewards with donations
        """
        self.init_projects()
        rewards = RewardFactory.create_batch(4)
        failed_donation = DonationFactory.create(reward=rewards[0], project=rewards[0].project)
        failed_donation.order.failed()
        failed_donation.order.save()
        failed_donation.save()
        donation = DonationFactory.create(reward=rewards[1], project=rewards[1].project)
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()
        donation.save()

        # Can't delete reward with successful donations
        with self.assertRaises(ValueError):
            rewards[1].delete()

        # Deleting other rewards is fine
        self.assertEquals(rewards[0].delete()[0], 1)
        self.assertEquals(rewards[2].delete()[0], 1)

        # There should still be two rewards
        self.assertEquals(Reward.objects.count(), 2)

        # There should still be one donation with reward
        self.assertEquals(Donation.objects.filter(reward__isnull=False).count(), 1)

        # Both donations should still be there
        self.assertEquals(Donation.objects.count(), 2)
