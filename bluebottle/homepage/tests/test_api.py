from datetime import timedelta
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.utils import LanguageFactory

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase

from rest_framework import status

from apps.fund.models import Donation, DonationStatuses, Order


class HomepageTestCase(BluebottleTestCase):
    """ Test that the homepage doesn't error out if no/a campaign is available """

    def setUp(self):
        super(HomepageTestCase, self).setUp()

        self.init_projects()

        # Create and activate user.
        self.user = BlueBottleUserFactory.create(email='johndoe@example.com', primary_language='en')
        title = u'Mobile payments for everyone 2!'
        language = LanguageFactory.create(code='en')

        self.project = ProjectFactory.create(title=title, slug=slugify(title), amount_asked=100000, owner=self.user)
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.is_campaign = True
        self.project.money_donated = 0
        self.project.language = language
        self.project.save()

        self.homepage_url = '/api/homepage/en'

