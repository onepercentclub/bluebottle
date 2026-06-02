from contextlib import contextmanager

import mock

from bluebottle.test.utils import BluebottleTestCase

_STRIPE_GUARD_MSG = (
    "Unexpected Stripe API request in tests (network disabled). "
    "Patch stripe.* calls or use factories from bluebottle.funding_stripe.tests.factories."
)


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
