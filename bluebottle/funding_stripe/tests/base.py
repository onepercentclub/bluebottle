from contextlib import contextmanager

import mock
import munch
import stripe

from bluebottle.test.utils import BluebottleTestCase

_STRIPE_GUARD_MSG = (
    "Unexpected Stripe API request in tests (network disabled). "
    "Patch stripe.* calls or use factories from bluebottle.funding_stripe.tests.factories."
)


COUNTRY_SPEC = stripe.CountrySpec('NL')
COUNTRY_SPEC.update(
    {
        "supported_bank_account_currencies": ['EUR'],
        "verification_fields": munch.munchify(
            {
                "individual": munch.munchify(
                    {
                        "additional": ["individual.verification.document"],
                        "minimum": ["individual.first_name"],
                    }
                )
            }
        )
    }
)


def _stripe_connect_account_stub_for_prefill(account_id="test-account-id"):
    account = stripe.Account(account_id)
    account.business_type = "individual"
    account.business_profile = munch.munchify({
        "mcc": "8398",
        "product_description": "Not applicable - test account.",
        "url": "https://goodup.com",
    })
    account.email = "stripe-test@example.com"
    account.company = None
    return account


@contextmanager
def stripe_payout_account_stripe_api_patches(account_id="test-account-id"):
    stub = _stripe_connect_account_stub_for_prefill(account_id)
    with mock.patch("stripe.CountrySpec.retrieve", return_value=COUNTRY_SPEC), \
            mock.patch("stripe.Account.retrieve", return_value=stub), \
            mock.patch("stripe.Account.modify", return_value=stub):
        yield


def save_stripe_payout_account(payout_account):
    account_id = payout_account.account_id or "test-account-id"
    with stripe_payout_account_stripe_api_patches(account_id):
        payout_account.save()


def _stripe_guard_denied(*args, **kwargs):
    raise RuntimeError(_STRIPE_GUARD_MSG)


@contextmanager
def patch_stripe_connect_account_api(account_object):
    with mock.patch("stripe.Account.retrieve", return_value=account_object), mock.patch(
        "stripe.Account.modify", return_value=account_object
    ):
        yield


def start_stripe_network_guard():
    try:
        from stripe._api_requestor import _APIRequestor
    except ImportError:
        return []
    patchers = []
    for name in ("request", "request_stream", "request_raw"):
        if hasattr(_APIRequestor, name):
            patcher = mock.patch.object(
                _APIRequestor,
                name,
                side_effect=_stripe_guard_denied,
            )
            patcher.start()
            patchers.append(patcher)
    for name in ("request_async", "request_stream_async", "request_raw_async"):
        if hasattr(_APIRequestor, name):
            async_mock = mock.AsyncMock(side_effect=RuntimeError(_STRIPE_GUARD_MSG))
            patcher = mock.patch.object(_APIRequestor, name, new=async_mock)
            patcher.start()
            patchers.append(patcher)
    return patchers


class FundingStripeMixin(object):
    def setUp(self):
        self._stripe_network_guard_patchers = start_stripe_network_guard()
        super().setUp()

    def tearDown(self):
        try:
            super().tearDown()
        finally:
            for patcher in reversed(getattr(self, "_stripe_network_guard_patchers", ())):
                patcher.stop()


class FundingStripeTestCase(FundingStripeMixin, BluebottleTestCase):
    pass
