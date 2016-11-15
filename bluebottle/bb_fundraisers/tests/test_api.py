import json
from django.core.files import File

from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory


class FundraiserAPITestCase(BluebottleTestCase):
    """ API tests for fundraisers """

    def setUp(self):
        super(FundraiserAPITestCase, self).setUp()

        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.some_other_user = BlueBottleUserFactory.create()
        self.some__other_token = "JWT {0}".format(
            self.some_other_user.get_jwt_token())

        self.some_project = ProjectFactory.create(
            owner=self.some_user,
            deadline=timezone.now() + timezone.timedelta(days=15))
        self.some_other_project = ProjectFactory.create(
            owner=self.some_user,
            deadline=timezone.now() + timezone.timedelta(days=15))

        self.image = File(open('./bluebottle/bb_fundraisers/test_images/upload.png'))

    def test_fundraiser_deadline_exceeds_project_deadline(self):
        future_date = self.some_project.deadline + timezone.timedelta(days=5)

        fundraiser_data = {
            'owner': self.some_user.pk,
            'project': self.some_project.slug,
            'title': 'Testing fundraisers',
            'description': 'Lorem Ipsum',
            'image': self.image,
            'amount': json.dumps({'amount': 1000, 'currency': 'EUR'}),
            'deadline': str(future_date)
        }

        response = self.client.post(reverse('fundraiser-list'),
                                    fundraiser_data,
                                    token=self.some_token,
                                    format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content).get('deadline', None)[0],
                         _('Fundraiser deadline exceeds project deadline.'))

    def test_fundraiser_deadline_not_exceeds_project_deadline(self):
        future_date = self.some_other_project.deadline - timezone.timedelta(days=5)

        fundraiser_data = {
            'owner': self.some_other_user.pk,
            'project': self.some_other_project.slug,
            'title': 'Testing fundraisers',
            'description': 'Lorem Ipsum',
            'image': self.image,
            'amount': json.dumps({'amount': 1000, 'currency': 'EUR'}),
            'deadline': str(future_date)
        }

        response = self.client.post(reverse('fundraiser-list'),
                                    fundraiser_data,
                                    token=self.some_token,
                                    format='multipart')
        self.assertEqual(response.status_code, 201)

    def test_fundraiser_currency_does_not_match(self):
        future_date = self.some_other_project.deadline - timezone.timedelta(days=5)

        fundraiser_data = {
            'owner': self.some_other_user.pk,
            'project': self.some_other_project.slug,
            'title': 'Testing fundraisers',
            'description': 'Lorem Ipsum',
            'image': self.image,
            'amount': json.dumps({'amount': 1000, 'currency': 'USD'}),
            'deadline': str(future_date)
        }

        response = self.client.post(reverse('fundraiser-list'),
                                    fundraiser_data,
                                    token=self.some_token,
                                    format='multipart')
        self.assertEqual(response.status_code, 400)
