from datetime import timedelta

import dateutil
from django.urls import reverse
from django.utils.timezone import localtime, now
from rest_framework import status

from bluebottle.activity_links.tests.factories import (
    LinkedFundingFactory, LinkedCollectCampaignFactory, LinkedDeedFactory,
    LinkedGrantApplicationFactory, LinkedDeadlineActivityFactory, LinkedDateActivityFactory,
    LinkedDateSlotFactory, LinkedPeriodicActivityFactory, LinkedScheduleActivityFactory,
)
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, APITestCase


class LinkedActivityImageAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(LinkedActivityImageAPITestCase, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.linked = LinkedFundingFactory.create(
            image=ImageFactory.create(owner=self.user),
        )

    def test_linked_activity_image_endpoint(self):
        url = reverse(
            'activity-links:image',
            args=(self.linked.pk, '200x200'),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_linked_activity_image_not_found(self):
        url = reverse('activity-links:image', args=(99999, '200x200'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LinkDetailAPITestMixin:
    factory = None
    other_factory = LinkedCollectCampaignFactory
    url_name = None
    resource_name = None

    def setUp(self):
        super().setUp()
        self.model = self.factory.create()
        self.url = reverse(f'activity-links:{self.url_name}', args=(self.model.pk,))

    def test_get(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        data = self.response.json()['data']
        self.assertEqual(data['id'], str(self.model.pk))
        self.assertEqual(data['type'], self.resource_name)

        self.assertAttribute('title', self.model.title)
        self.assertAttribute('link', self.model.link)
        self.assertMeta('current-status', {
            'value': 'open',
            'name': 'Open',
            'description': self.model.states.current_state.description,
        })

    def test_get_logged_in(self):
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

    def test_get_not_found(self):
        self.url = reverse(f'activity-links:{self.url_name}', args=(99999,))
        self.perform_get()

        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_get_other_link_type(self):
        other = self.other_factory.create()
        self.url = reverse(f'activity-links:{self.url_name}', args=(other.pk,))
        self.perform_get()

        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_get_closed_platform_anonymous(self):
        MemberPlatformSettings.objects.update_or_create(closed=True)
        self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_platform_logged_in(self):
        MemberPlatformSettings.objects.update_or_create(closed=True)
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)


class LocationLinkDetailAPITestMixin(LinkDetailAPITestMixin):
    end_attribute = 'end'

    def test_get_location(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('start')
        self.assertAttribute(self.end_attribute)
        self.assertRelationship('location', [self.model.location])
        self.assertIncluded('location', self.model.location)


class DeedLinkDetailAPITestCase(LinkDetailAPITestMixin, APITestCase):
    factory = LinkedDeedFactory
    url_name = 'deed-activity-link'
    resource_name = 'activities/deed-links'

    def test_get_dates(self):
        self.perform_get()

        self.assertAttribute('start')
        self.assertAttribute('end')


class CollectLinkDetailAPITestCase(LocationLinkDetailAPITestMixin, APITestCase):
    factory = LinkedCollectCampaignFactory
    other_factory = LinkedDeedFactory
    url_name = 'collect-activity-link'
    resource_name = 'activities/collect-links'

    def test_get_collect_attributes(self):
        self.model.collect_type = 'Clothes'
        self.model.location_hint = 'Behind the building'
        self.model.save()
        self.perform_get()

        self.assertAttribute('collect_type', 'Clothes')
        self.assertAttribute('location_hint', 'Behind the building')


class FundingLinkDetailAPITestCase(LinkDetailAPITestMixin, APITestCase):
    factory = LinkedFundingFactory
    url_name = 'funding-activity-link'
    resource_name = 'activities/funding-links'

    def test_get_amounts(self):
        self.perform_get()

        self.assertAttribute('target')
        self.assertAttribute('amount_raised')


class GrantApplicationLinkDetailAPITestCase(LinkDetailAPITestMixin, APITestCase):
    factory = LinkedGrantApplicationFactory
    url_name = 'grant-application-activity-link'
    resource_name = 'activities/grant-application-links'

    def test_get_target(self):
        self.perform_get()

        self.assertAttribute('target')


class DeadlineLinkDetailAPITestCase(LocationLinkDetailAPITestMixin, APITestCase):
    factory = LinkedDeadlineActivityFactory
    url_name = 'deadline-activity-link'
    resource_name = 'activities/deadline-links'
    end_attribute = 'deadline'

    def test_get_duration(self):
        self.perform_get()

        self.assertAttribute('duration')

    def test_get_deadline(self):
        self.perform_get()

        self.assertAttribute('deadline', str(localtime(self.model.end).date()))

    def test_get_no_deadline(self):
        self.model.end = None
        self.model.save()
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('deadline')
        self.assertIsNone(self.response.json()['data']['attributes']['deadline'])


class DateLinkDetailAPITestCase(LinkDetailAPITestMixin, APITestCase):
    factory = LinkedDateActivityFactory
    url_name = 'date-activity-link'
    resource_name = 'activities/date-links'

    def test_get_slots(self):
        slots = LinkedDateSlotFactory.create_batch(2, activity=self.model)
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertRelationship('slots', slots)
        for slot in slots:
            self.assertIncluded('slots', slot)

    def test_get_no_slots(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('slot_count')
        self.assertEqual(self.response.json()['data']['attributes']['slot-count'], 0)
        self.assertAttribute('date_info', {
            'total': 0,
            'has_multiple': False,
            'is_full': False,
            'count': 0,
            'first': None,
            'end': None,
            'duration': None,
            'capacity': None,
            'spots_left': None,
        })

    def test_get_single_slot(self):
        slot = LinkedDateSlotFactory.create(activity=self.model)
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('slot_count', 1)
        date_info = self.response.json()['data']['attributes']['date-info']
        self.assertEqual(date_info['total'], 1)
        self.assertEqual(date_info['count'], 1)
        self.assertFalse(date_info['has_multiple'])
        self.assertEqual(dateutil.parser.parse(date_info['first']), slot.start)
        self.assertEqual(dateutil.parser.parse(date_info['end']), slot.end)
        self.assertIsNotNone(date_info['duration'])

    def test_get_multiple_slots(self):
        slots = [
            LinkedDateSlotFactory.create(
                activity=self.model,
                start=now() + timedelta(days=days),
                end=now() + timedelta(days=days, hours=2),
            )
            for days in (2, 4, 6)
        ]
        LinkedDateSlotFactory.create(
            activity=self.model,
            start=now() - timedelta(days=10),
            end=now() - timedelta(days=10, hours=-2),
        )
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('slot_count', 3)
        date_info = self.response.json()['data']['attributes']['date-info']
        self.assertEqual(date_info['total'], 4)
        self.assertEqual(date_info['count'], 3)
        self.assertTrue(date_info['has_multiple'])
        self.assertEqual(date_info['first'], str(slots[0].start.date()))
        self.assertEqual(date_info['end'], str(slots[-1].end.date()))
        self.assertIsNone(date_info['duration'])

    def test_get_only_past_slots(self):
        LinkedDateSlotFactory.create_batch(
            2,
            activity=self.model,
            start=now() - timedelta(days=10),
            end=now() - timedelta(days=10, hours=-2),
        )
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('slot_count', 2)


class PeriodicLinkDetailAPITestCase(LocationLinkDetailAPITestMixin, APITestCase):
    factory = LinkedPeriodicActivityFactory
    url_name = 'periodic-activity-link'
    resource_name = 'activities/periodic-links'
    end_attribute = 'deadline'

    def test_get_period(self):
        self.model.period = 'weeks'
        self.model.save()
        self.perform_get()

        self.assertAttribute('period', 'weeks')


class ScheduleLinkDetailAPITestCase(LocationLinkDetailAPITestMixin, APITestCase):
    factory = LinkedScheduleActivityFactory
    url_name = 'schedule-activity-link'
    resource_name = 'activities/schedule-links'
    end_attribute = 'deadline'
