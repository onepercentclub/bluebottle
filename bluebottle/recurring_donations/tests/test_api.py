from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.geo.models import Country
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class MonthlyDonationApiTest(BluebottleTestCase):
    def setUp(self):
        super(MonthlyDonationApiTest, self).setUp()
        self.init_projects()

        self.phase_campaign = ProjectPhase.objects.get(slug='campaign')
        self.country = CountryFactory()

        self.some_project = ProjectFactory.create(amount_asked=500,
                                                  status=self.phase_campaign)
        self.another_project = ProjectFactory.create(amount_asked=750,
                                                     status=self.phase_campaign)

        self.some_user = BlueBottleUserFactory.create()
        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())
        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(
            self.another_user.get_jwt_token())

        self.monthly_donation_url = reverse('monthly-donation-list')
        self.monthly_donation_project_url = reverse(
            'monthly-donation-project-list')

        self.monthly_profile = {'iban': 'NL13TEST0123456789',
                                'bic': 'TESTNL2A',
                                'name': 'Nijntje het Konijntje',
                                'city': 'Amsterdam',
                                'country': self.country.id,
                                'amount': 50}

    def test_create_monthly_donation(self):
        """
        Tests for creating, retrieving, updating monthly donation.
        """

        # Check that user has no monthly donation
        response = self.client.get(self.monthly_donation_url,
                                   token=self.some_user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

        # Create a new monthly donation
        response = self.client.post(self.monthly_donation_url,
                                    self.monthly_profile,
                                    token=self.some_user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEqual(response.data['amount'],
                         self.monthly_profile['amount'])
        self.assertEqual(response.data['active'], True)
        import ipdb;ipdb.set_trace()
        some_monthly_donation_id = response.data['id']

        # Reload it and check that all is still well.
        response = self.client.get(self.monthly_donation_url,
                                   token=self.some_user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['amount'],
                         self.monthly_profile['amount'])

        # Add a preferred projects
        monthly_project = {
            'donation': some_monthly_donation_id,
            'project': self.some_project.slug
        }
        response = self.client.post(self.monthly_donation_project_url,
                                    monthly_project, token=self.some_user_token)
        import ipdb;ipdb.set_trace()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)

        # Reload it. It should have that project embedded
        response = self.client.get(self.monthly_donation_url,
                                   token=self.some_user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(len(response.data['results'][0]['projects']), 1)
        self.assertEqual(response.data['results'][0]['projects'][0]['project'],
                         self.some_project.slug)


        # Another should not have a monthly donation
        response = self.client.get(self.monthly_donation_url,
                                   token=self.another_user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 0)

        # Another user can't add a project to first monthly donation
        monthly_project = {
            'donation': some_monthly_donation_id,
            'project': self.another_project.slug
        }
        response = self.client.post(self.monthly_donation_project_url,
                                    monthly_project,
                                    token=self.another_user_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         response.data)
