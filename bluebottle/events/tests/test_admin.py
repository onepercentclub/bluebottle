# -*- coding: utf-8 -*-
from builtins import str
from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestEventAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestEventAdmin, self).setUp()
        self.site = AdminSite()
        self.event = EventFactory.create(
            registration_deadline=(now() + timedelta(weeks=2)).date(),
            status='created'
        )
        self.event_url = reverse('admin:events_event_change', args=(self.event.id,))
        self.event.save()

    def test_event_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_event_admin(self):
        self.client.force_login(self.superuser)
        ParticipantFactory.create_batch(3, activity=self.event)
        url = reverse('admin:events_event_delete', args=(self.event.id,))
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Participant.objects.count(), 0)

    def test_delete_participant_event_admin(self):
        self.client.force_login(self.superuser)
        self.participants = ParticipantFactory.create_batch(3, activity=self.event)
        self.assertEqual(Participant.objects.count(), 3)
        url = reverse('admin:events_event_change', args=(self.event.id,))

        data = {
            'title': 'New title',
            'slug': self.event.slug,
            'owner': self.event.owner_id,
            'initiative': self.event.initiative_id,
            'description': self.event.description,
            'capacity': self.event.capacity,
            'start_0': str(self.event.start.date()),
            'start_1': str(self.event.start.time()),
            'duration': self.event.duration,
            'status': self.event.status,
            'registration_deadline': str(self.event.registration_deadline),
            'is_online': self.event.is_online,
            'location': self.event.location_id,
            'location_hint': self.event.location_hint,

            '_continue': 'Save and continue editing',
            'confirm': 'Yes',

            'follow-follow-content_type-instance_id-INITIAL_FORMS': '0',
            'follow-follow-content_type-instance_id-TOTAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-TOTAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-INITIAL_FORMS': '0',
            'notifications-message-content_type-object_id-TOTAL_FORMS': '0',
            'notifications-message-content_type-object_id-INITIAL_FORMS': '0',

            'contributions-TOTAL_FORMS': '3',
            'contributions-INITIAL_FORMS': '3',
            'contributions-0-contribution_ptr': self.participants[0].contribution_ptr_id,
            'contributions-0-activity': self.event.id,
            'contributions-0-user': self.participants[0].user_id,
            'contributions-0-time_spent': self.participants[0].time_spent,
            'contributions-0-DELETE': 'on',
            'contributions-1-contribution_ptr': self.participants[1].contribution_ptr_id,
            'contributions-1-activity': self.event.id,
            'contributions-1-user': self.participants[1].user_id,
            'contributions-1-time_spent': self.participants[1].time_spent,
            'contributions-2-contribution_ptr': self.participants[2].contribution_ptr_id,
            'contributions-2-activity': self.event.id,
            'contributions-2-user': self.participants[2].user_id,
            'contributions-2-time_spent': self.participants[2].time_spent,
            'contributions-2-DELETE': 'on',
        }

        response = self.client.post(url, data)
        self.assertEqual(
            response.status_code, status.HTTP_302_FOUND,
            'Deleting participants failed. '
            'Did you change admin fields for EventAdmin? '
            'Please adjust the data in this test.')
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'New title')
        self.assertEqual(Participant.objects.count(), 1)
