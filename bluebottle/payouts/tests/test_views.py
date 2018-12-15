from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory
from bluebottle.test.utils import BluebottleTestCase


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret'
    }
]

ACCOUNT_UPDATE = {
  "created": 1326853478,
  "livemode": False,
  "id": "account.updated_00000000000000",
  "type": "account.updated",
  "object": "event",
  "request": None,
  "pending_webhooks": 1,
  "api_version": "2018-11-08",
  "data": {
    "object": {
      "id": "acct_00000000000000",
      "object": "account",
      "business_logo": "file_1DVbybK7fTZ9PRZU6S2gt7Rb",
      "business_name": "GoodUp BV",
      "business_primary_color": "#5555fe",
      "business_url": "https://goodup.com",
      "charges_enabled": True,
      "country": "NL",
      "created": 1542013940,
      "debit_negative_balances": None,
      "decline_charge_on": {
        "avs_failure": False,
        "cvc_failure": True
      },
      "default_currency": "eur",
      "details_submitted": True,
      "display_name": "GoodUp",
      "email": "test@stripe.com",
      "external_accounts": {
        "object": "list",
        "data": [
          {
            "id": "ba_00000000000000",
            "object": "bank_account",
            "account": "acct_00000000000000",
            "account_holder_name": None,
            "account_holder_type": None,
            "bank_name": "RABOBANK NEDERLAND",
            "country": "NL",
            "currency": "eur",
            "default_for_currency": True,
            "fingerprint": "kjdsfghksdfh",
            "last4": "1234",
            "metadata": {
            },
            "routing_number": "RABONL2U",
            "status": "new"
          }
        ],
        "has_more": False,
        "total_count": 1,
        "url": "/v1/accounts/acct_54763245876/external_accounts"
      },
      "legal_entity": {
        "address": {
          "city": "Amsterdam",
          "country": "NL",
          "line1": "'s Gravenhekje 1A",
          "line2": None,
          "postal_code": "1011TG",
          "state": "NH"
        },
        "business_name": "GoodUp BV",
        "business_tax_id_provided": True,
        "business_vat_id_provided": True,
        "dob": {
          "day": 11,
          "month": 3,
          "year": 1975
        },
        "first_name": "Bart",
        "last_name": "Lacroix",
        "personal_address": {
          "city": "Amsterdam",
          "country": "NL",
          "line1": "Prinseneiland 55C",
          "line2": None,
          "postal_code": "1013LM",
          "state": "NH"
        },
        "type": "company",
        "verification": {
          "details": "No ID scan was uploaded",
          "details_code": None,
          "document": None,
          "document_back": None,
          "status": "verified"
        }
      },
      "metadata": {
      },
      "payout_schedule": {
        "delay_days": 7,
        "interval": "daily"
      },
      "payout_statement_descriptor": None,
      "payouts_enabled": True,
      "product_description": "Tralala.",
      "shortform_statement_descriptor_prefix": "",
      "statement_descriptor": "TEST",
      "statement_descriptor_prefix": "",
      "support_address": {
        "city": "Amsterdam",
        "country": "NL",
        "line1": "'s Gravenhekje 1A",
        "line2": None,
        "postal_code": "1011TG",
        "state": None
      },
      "support_email": "bart@goodup.com",
      "support_phone": "+31207158980",
      "support_url": "",
      "timezone": "Europe/Amsterdam",
      "tos_acceptance": {
        "date": 1542015026,
        "iovation_blackbox": "KDJFHGKDJFGH",
        "ip": "213.127.165.114",
        "user_agent": None
      },
      "type": "standard",
      "verification": {
        "disabled_reason": None,
        "due_by": None,
      }
    },
    "previous_attributes": {
      "verification": {
        "fields_needed": [
        ],
        "due_by": None
      }
    }
  }
}

BANK_ACCOUNT_UPDATE = {
  "created": 1326853478,
  "livemode": False,
  "id": "account.external_00000000000000",
  "type": "account.external_account.updated",
  "object": "event",
  "request": None,
  "pending_webhooks": 1,
  "api_version": "2018-11-08",
  "data": {
    "object": {
      "id": "ba_00000000000000",
      "object": "bank_account",
      "account": "acct_00000000000000",
      "account_holder_name": "Jane Austen",
      "account_holder_type": "individual",
      "bank_name": "STRIPE TEST BANK",
      "country": "US",
      "currency": "eur",
      "default_for_currency": False,
      "fingerprint": "Fn8WwZ7vTDkXWCpw",
      "last4": "6789",
      "metadata": {
      },
      "routing_number": "110000000",
      "status": "new"
    },
    "previous_attributes": {
      "description": "Old description"
    }
  }
}


@override_settings(
    MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS
)
class StripePayoutAccountUpdateTestCase(BluebottleTestCase):
    def setUp(self):
        self.payout_account = StripePayoutAccountFactory.create(
            account_id='acct_00000000000035'
        )

        class MockEvent(object):
            def __init__(self, type, object):
                self.type = type

                for key, value in object.items():
                    setattr(self.data.object, key, value)

            class data:
                class object:
                    pass

        self.MockEvent = MockEvent

    def test_update_account(self):
        """
        Test Stripe payout account update
        """
        with patch(
            'stripe.Webhook.construct_event',
            return_value=self.MockEvent(
                'account.updated', {'id': self.payout_account.account_id}
            )
        ):
            with patch(
                'bluebottle.payouts.models.StripePayoutAccount.check_status'
            ) as check_status:
                response = self.client.post(
                    reverse('stripe-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, 200)
                check_status.assert_called_once()
