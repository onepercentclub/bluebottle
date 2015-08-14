from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
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
        self.donation = DonationFactory(order=self.order, amount=35, fundraiser=None, project=self.project1)


    def test_system_wallpost_project_after_donation(self):
        """ Test that a SystemWallpost is created for the project wall when a user does a succesful donation """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        self.order.locked()
        self.order.succeeded()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].content_object, self.project1)
        self.assertEqual(SystemWallpost.objects.all()[0].author, self.order.user)


    def test_system_wallpost_fundraiser_after_donation(self):
        """ Test that a SystemWallpost is created for the project and fundraiser wall when a user does a succesful donation """
        self.assertEqual(SystemWallpost.objects.count(), 0)

        order = OrderFactory.create(user=self.user1)
        fundraiser = FundraiserFactory(project=self.project1)
        donation2 = DonationFactory(order=order, amount=35, project=self.project1, fundraiser=fundraiser)

        order.locked()
        order.succeeded()

        self.assertEqual(SystemWallpost.objects.count(), 2)
        self.assertEqual(SystemWallpost.objects.all()[1].content_object, fundraiser)
        self.assertEqual(SystemWallpost.objects.all()[1].author, order.user)

    def test_anonymous_donation_no_author_on_wallpost(self):
        """ Test that a SystemWallpost is created without an author when a donation is anonymous"""
        self.assertEqual(SystemWallpost.objects.count(), 0)

        order = OrderFactory.create(user=self.user1)
        donation2 = DonationFactory(order=order, amount=35, project=self.project1, fundraiser=None, anonymous=True)

        order.locked()
        order.succeeded()

        self.assertEqual(SystemWallpost.objects.count(), 1)
        self.assertEqual(SystemWallpost.objects.all()[0].author, None)


