# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from rest_framework import status

from bluebottle.events.admin import EventAdmin
from bluebottle.events.models import Event
from bluebottle.events.tests.factories import EventFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestEventAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestEventAdmin, self).setUp()
        self.site = AdminSite()
        self.event_admin = EventAdmin(Event, self.site)
        self.event = EventFactory.create(status='created')
        self.event_url = reverse('admin:events_event_change', args=(self.event.id,))
        self.event.save()

    def test_event_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
