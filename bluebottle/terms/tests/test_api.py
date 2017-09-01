from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.terms import TermsFactory


class TermsAPITest(BluebottleTestCase):
    """ Integration tests for the Terms API. """

    def setUp(self):
        super(TermsAPITest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = 'JWT {0}'.format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()
        self.user_2_token = 'JWT {0}'.format(self.user_2.get_jwt_token())

        self.terms = TermsFactory.create(contents='Awesome terms!')

    def test_get_current_terms(self):
        response = self.client.get(reverse('current-terms'))

        self.assertEqual(response.data['contents'], self.terms.contents)

    def test_agree_terms(self):
        response = self.client.post(reverse('terms-agreement-list'),
                                    token=self.user_2_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user_2.id)
        self.assertEqual(response.data['terms'], self.terms.id)
