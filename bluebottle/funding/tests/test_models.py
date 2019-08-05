from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingTestCase(BluebottleTestCase):

    def test_absolute_url(self):
        funding = FundingFactory()
        expected = 'http://testserver/en/initiatives/activities/details' \
                   '/funding/{}/{}'.format(funding.id, funding.slug)
        self.assertEqual(funding.get_absolute_url(), expected)
