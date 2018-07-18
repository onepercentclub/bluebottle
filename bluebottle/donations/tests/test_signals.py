from django.core import mail

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.wallposts.models import SystemWallpost


class TestDonationSignals(BluebottleTestCase):
    def setUp(self):
        super(TestDonationSignals, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.init_projects()
        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.project1.set_status('campaign')
        self.order = OrderFactory.create(user=self.user1)
        self.donation = DonationFactory(order=self.order, amount=35,
                                        fundraiser=None, project=self.project1)

    def test_successfull_donation(self):
        """
        Test that a SystemWallpost is created for the project wall
        when a user does a succesful donation
        """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].content_object,
                         self.project1)
        self.assertEqual(SystemWallpost.objects.all()[0].author,
                         self.order.user)

        self.assertEqual(len(mail.outbox), 2)

    def test_successfull_donation_only_once(self):
        """
        Test that a SystemWallpost is created for the project wall
        when a user does a succesful donation
        """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()
        self.order.failed()
        self.order.success()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].content_object,
                         self.project1)
        self.assertEqual(SystemWallpost.objects.all()[0].author,
                         self.order.user)

        self.assertEqual(len(mail.outbox), 2)

    def test_successfull_fundraiser_donation(self):
        """
        Test that a SystemWallpost is created for the fundraiser
        wall only when a user does a succesful donation
        """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        order = OrderFactory.create(user=self.user1)
        fundraiser = FundraiserFactory(project=self.project1)
        DonationFactory(order=order, amount=35,
                        project=self.project1, fundraiser=fundraiser)

        order.locked()
        order.save()
        order.success()
        order.save()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].content_object,
                         fundraiser)
        self.assertEqual(SystemWallpost.objects.all()[0].author, order.user)
        self.assertEqual(len(mail.outbox), 3)

    def test_successfull_anonymous_donation(self):
        """
        Test that a SystemWallpost is created without an author when a donation is anonymous
        """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        order = OrderFactory.create(user=self.user1)
        DonationFactory(order=order, amount=35, project=self.project1,
                        fundraiser=None, anonymous=True)

        order.locked()
        order.save()
        order.success()
        order.save()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].author, None)
        self.assertEqual(len(mail.outbox), 2)
