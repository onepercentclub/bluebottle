from unittest import mock

from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.effects import CreateEffect, UpdateEventEffect
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.utils import BluebottleTestCase


class FederationEffectFailureTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.funding = FundingFactory.create()
        self.error = ValidationError({'location': {'name': ['Dit veld mag niet leeg zijn.']}})

    def run_effect(self, effect_class):
        with mock.patch(
            'bluebottle.activity_pub.effects.adapter.create_or_update_event',
            side_effect=self.error
        ):
            with mock.patch('bluebottle.activity_pub.effects.logger') as logger:
                effect_class(self.funding).post_save()

        logger.exception.assert_called_once()
        self.assertIn(self.funding.pk, logger.exception.call_args.args)

    def test_create_effect_does_not_raise_on_federation_error(self):
        self.run_effect(CreateEffect)

    def test_update_event_effect_does_not_raise_on_federation_error(self):
        self.run_effect(UpdateEventEffect)
