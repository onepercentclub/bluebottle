import json
import mock

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from django.core.urlresolvers import reverse

class TestShareFlyer(BluebottleTestCase):
    def setUp(self):
        super(TestShareFlyer, self).setUp()
        self.init_projects()
        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())
        self.project = ProjectFactory.create()

    def test_preview(self):
        """ simple preview of project flyer """
        response = self.client.get(
            reverse("share_flyer", kwargs={'slug':self.project.slug}),
            HTTP_AUTHORIZATION=self.user_1_token
        )
        data = json.loads(response.content)
        self.assertTrue('preview' in data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch("bluebottle.utils.views.send_mail")
    def test_share_success(self, send_mail):
        """ successfull share of project flyer """
        response = self.client.post(
            reverse("share_flyer", kwargs={'slug':self.project.slug}),
            HTTP_AUTHORIZATION=self.user_1_token,
            data={"share_name":"S. Hare",
                  "share_email":"share@example.com",
                  "share_motivation":"Wow I'm sharing this project!",
                  "share_cc":False}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.failUnless(send_mail.called)

    @mock.patch("bluebottle.utils.views.send_mail")
    def test_share_fail(self, send_mail):
        """ failed share due to missing email """
        response = self.client.post(
            reverse("share_flyer", kwargs={'slug':self.project.slug}),
            HTTP_AUTHORIZATION=self.user_1_token,
            data={"share_name": "S. Hare",
                  "share_motivation":"Wow I'm sharing this project!",
                  "share_cc":True}
        )
        data = json.loads(response.content)
        self.assertTrue('share_email' in data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.failIf(send_mail.called)

    @mock.patch("bluebottle.utils.views.send_mail")
    def test_share_cc(self, send_mail):
        """ successfull share of project flyer, with cc """
        response = self.client.post(
            reverse("share_flyer", kwargs={'slug':self.project.slug}),
            HTTP_AUTHORIZATION=self.user_1_token,
            data={"share_name":"S. Hare",
                  "share_email":"share@example.com",
                  "share_motivation":"Wow I'm sharing this project!",
                  "share_cc":True}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.failUnless(send_mail.called)
        self.failUnless(self.user_1.email in send_mail.call_args[1].get('cc'))
