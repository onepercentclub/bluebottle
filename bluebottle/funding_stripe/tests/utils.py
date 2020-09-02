import bunch
import stripe
from mock import patch

from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


def generate_stripe_payout_account(account_id='some-id', owner=None):
    if not owner:
        owner = BlueBottleUserFactory.create()
    account = StripePayoutAccount(
        owner=owner,
        country='NL',
        account_id=account_id
    )
    stripe_account = stripe.Account(account_id)
    stripe_account.update({
        'country': 'NL',
        'individual': bunch.bunchify({
            'first_name': 'Jhon',
            'last_name': 'Example',
            'email': 'jhon@example.com',
            'verification': {
                'status': 'verified',
            },
            'requirements': bunch.bunchify({
                'eventually_due': [
                    'external_accounts',
                    'individual.verification.document',
                    'document_type',
                ]
            }),
        }),
        'requirements': bunch.bunchify({
            'eventually_due': [
                'external_accounts',
                'individual.verification.document.front',
                'document_type',
            ],
            'disabled': False
        }),
        'external_accounts': bunch.bunchify({
            'total_count': 0,
            'data': []
        })
    })
    with patch('stripe.Account.retrieve', return_value=stripe_account):
        account.save()
    return account
