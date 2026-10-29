from future import standard_library

from bluebottle.members.models import MemberPlatformSettings, SocialLoginSettings

standard_library.install_aliases()
import json
import logging

import httmock
import mock
from django.urls import reverse
from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


@httmock.urlmatch(netloc="graph.facebook.com", path=r"/[v0-9\.]+/me")
def facebook_me_mock(url, request):
    return json.dumps(
        {"first_name": "First", "last_name": "Last", "email": "test@goodup.com"}
    )


def load_signed_request_mock(self, signed_request):
    _key, secret = self.get_key_and_secret()

    if signed_request == "test-signed-request" and secret == "test-secret":
        return {"user_id": 1}
    else:
        return {}


class SocialTokenAPITestCase(BluebottleTestCase):
    """
    Test the social authorization token api endpoint
    """

    def setUp(self):
        super(SocialTokenAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.token_url = reverse("social-login")
        self.client = JSONAPITestClient()

        settings = MemberPlatformSettings.load()

        self.settings, _create = SocialLoginSettings.objects.update_or_create(
            backend="facebook",
            defaults={
                'secret': "test-secret",
                'client_id': "test-client-id",
                'settings': settings,
            }
        )

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    "data": {
                        "type": "social/tokens",
                        "attributes": {
                            "backend": "facebook",
                            "access-token": "test_token",
                            "signed-request": "test-signed-request",
                        },
                    }
                },
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue("token" in response.json()["data"]["attributes"])

            authenticated_response = self.client.get(
                reverse("current-member-detail"),
                HTTP_AUTHORIZATION="JWT {0}".format(
                    response.json()["data"]["attributes"]["token"]
                ),
            )

            self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                authenticated_response.json()["data"]["attributes"]["first-name"],
                "First",
            )
            self.assertEqual(
                authenticated_response.json()["data"]["attributes"]["last-name"], "Last"
            )

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_empty_email_address(self):
        @httmock.urlmatch(netloc="graph.facebook.com", path=r"/[v0-9\.]+/me")
        def facebook_me_mock(url, request):
            return json.dumps({"first_name": "First", "last_name": "Last", "email": ""})

        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    "data": {
                        "type": "social/tokens",
                        "attributes": {
                            "backend": "facebook",
                            "access-token": "test_token",
                            "signed-request": "test-signed-request",
                        },
                    }
                },
            )

            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(
                response.json()["errors"][0]["detail"],
                "Please allow Facebook access to your email address if you wish to sign up/log in via Facebook.",
            )

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_invalid_signed_request(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    "type": "social/tokens",
                    "attributes": {
                        "backend": "facebook",
                        "access-token": "test_token",
                        "signed-request": "test-invalid",
                    },
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_invalid_secret(self):
        self.settings.secret = "invalid-secret"
        self.settings.save()

        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    "type": "social/tokens",
                    "attributes": {
                        "backend": "facebook",
                        "access-token": "test_token",
                        "signed-request": "test-signed-request",
                    },
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_invalid_token(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    "type": "social/tokens",
                    "attributes": {
                        "backend": "facebook",
                        "access-token": "test_invalid_token",
                        "signed-request": "test-signed-request",
                    },
                },
                token=self.user_token,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_no_data(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(self.token_url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def enable_logging(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)

    def post_google_token(self):
        return self.client.post(
            self.token_url,
            {
                "data": {
                    "type": "social/tokens",
                    "attributes": {
                        "backend": "google",
                        "code": "test-code",
                    },
                }
            },
        )

    def assert_login_failed(self, response, logs, secret):
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errors"][0]["code"], "failed")
        self.assertFalse(any(secret in line for line in logs.output))

    @mock.patch(
        "social_core.backends.facebook.FacebookAppOAuth2.load_signed_request",
        return_value=None,
    )
    def test_token_unparseable_signed_request(self, _mock):
        self.enable_logging()
        with self.assertLogs("bluebottle.auth.views", level="WARNING") as logs:
            response = self.client.post(
                self.token_url,
                {
                    "data": {
                        "type": "social/tokens",
                        "attributes": {
                            "backend": "facebook",
                            "access-token": "test_token",
                            "signed-request": "garbage",
                        },
                    }
                },
            )
        self.assert_login_failed(response, logs, "test_token")

    @mock.patch(
        "bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request",
        load_signed_request_mock,
    )
    def test_token_facebook_graph_error(self):
        self.enable_logging()

        @httmock.urlmatch(netloc="graph.facebook.com")
        def facebook_error_mock(url, request):
            return httmock.response(500, "error", request=request)

        with httmock.HTTMock(facebook_error_mock):
            with self.assertLogs("bluebottle.auth.views", level="WARNING") as logs:
                response = self.client.post(
                    self.token_url,
                    {
                        "data": {
                            "type": "social/tokens",
                            "attributes": {
                                "backend": "facebook",
                                "access-token": "test_token",
                                "signed-request": "test-signed-request",
                            },
                        }
                    },
                )
        self.assert_login_failed(response, logs, "test_token")

    def test_token_google_token_endpoint_error(self):
        self.enable_logging()

        @httmock.all_requests
        def google_error_mock(url, request):
            return httmock.response(500, "error", request=request)

        with httmock.HTTMock(google_error_mock):
            with self.assertLogs("bluebottle.auth.views", level="WARNING") as logs:
                response = self.post_google_token()
        self.assert_login_failed(response, logs, "test-code")

    def test_token_google_invalid_grant(self):
        self.enable_logging()

        @httmock.all_requests
        def google_invalid_grant_mock(url, request):
            return httmock.response(
                400,
                json.dumps({"error": "invalid_grant"}),
                {"content-type": "application/json"},
                request=request,
            )

        with httmock.HTTMock(google_invalid_grant_mock):
            with self.assertLogs("bluebottle.auth.views", level="WARNING") as logs:
                response = self.post_google_token()
        self.assert_login_failed(response, logs, "test-code")
