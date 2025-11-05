# -*- coding: utf-8 -*-
from mock import patch

from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.models import FundingPlatformSettings
from bluebottle.funding.tests.factories import PayoutFactory
from bluebottle.grant_management.tests.factories import GrantPayoutFactory
from bluebottle.test.utils import BluebottleTestCase


class GrantPayoutStateMachineTests(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        # Disable IBAN check to simplify testing
        platform_settings = FundingPlatformSettings.load()
        platform_settings.enable_iban_check = False
        platform_settings.save()

    @patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout')
    def test_approve_transition_not_available_after_approval(self, mock_trigger_payout):
        """Test that after approving a GrantPayout, the 'approve' transition is no longer available."""
        payout = GrantPayoutFactory.create(status='new')
        
        # Initially, approve should be available
        payout.states.approve(save=True)
        self.assertEqual(payout.status, 'approved')
        
        # After approval, approve should not be available
        payout.refresh_from_db()
        with self.assertRaises(TransitionNotPossible):
            payout.states.approve(save=True)
