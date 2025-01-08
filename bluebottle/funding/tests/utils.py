from unittest import mock

import stripe

from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory


def generate_mock_bank_account():
    connect_account = stripe.StripeObject.construct_from({
        "id": "some-connect-id",
        "country": "NL",
        "requirements": stripe.StripeObject.construct_from({
            'current_deadline': None,
            'currently_due': [],
            'disabled_reason': None,
            'eventually_due': [],
            'past_due': [],
            'pending_verification': []
        }, stripe.api_key),
        "charges_enabled": True,
        "payouts_enabled": True,
    }, stripe.api_key)

    with mock.patch('stripe.Account.create', return_value=connect_account), \
            mock.patch('stripe.Account.modify', return_value=connect_account):
        bank_account = ExternalAccountFactory.create(
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id",
                status="verified"
            ),
        )
    return bank_account
