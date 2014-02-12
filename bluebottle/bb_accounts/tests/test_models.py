from django.test import TestCase

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class BlueBottleUserTest(TestCase):
    def test_create_user