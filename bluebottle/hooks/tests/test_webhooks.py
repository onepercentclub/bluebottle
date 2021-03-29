import json
from datetime import date, timedelta
from urllib.parse import urlparse
import httmock

from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.deeds.tests.factories import (
    DeedFactory, DeedParticipantFactory
)

from bluebottle.hooks.tests.factories import WebHookFactory


class DeedPeriodicTasksTestCase(BluebottleTestCase):
    factory = DeedFactory

    def setUp(self):
        super(DeedPeriodicTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')

        self.webhook = WebHookFactory.create()

        @httmock.urlmatch(netloc=r'{}$'.format(urlparse(self.webhook.url).netloc))
        def hook_mock(url, request):
            self.request = request
            return {'content': {}, 'status_code': status.HTTP_200_OK}

        self.hook_mock = hook_mock

        self.activity = self.factory.create(
            initiative=self.initiative,
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        with httmock.HTTMock(self.hook_mock):
            self.activity.states.submit(save=True)
            print(json.loads(self.request.body))

    def test_webhook(self):
        with httmock.HTTMock(self.hook_mock):
            DeedParticipantFactory(activity=self.activity)

        print(json.loads(self.request.body))
