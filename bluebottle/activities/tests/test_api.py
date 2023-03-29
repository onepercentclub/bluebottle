import re
import io
from builtins import str
import json
from datetime import timedelta, date
import dateutil
from openpyxl import load_workbook

from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from bluebottle.activities.models import Activity
from django_elasticsearch_dsl.test import ESTestCase
from rest_framework import status

from bluebottle.files.tests.factories import ImageFactory

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory

from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.activities.utils import TeamSerializer, InviteSerializer
from bluebottle.activities.serializers import TeamTransitionSerializer
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.offices.tests.factories import OfficeRegionFactory, OfficeSubRegionFactory
from bluebottle.time_based.serializers import PeriodParticipantSerializer
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory, DateParticipantFactory, PeriodParticipantFactory,
    DateActivitySlotFactory, SkillFactory, TeamSlotFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory, GeolocationFactory, PlaceFactory, CountryFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityListSearchAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ActivityListSearchAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.url = reverse('activity-preview-list')
        self.owner = BlueBottleUserFactory.create()

    def test_images(self):
        DateActivityFactory.create(
            owner=self.owner, status='open', image=ImageFactory.create()
        )
        PeriodActivityFactory.create(status='open', image=ImageFactory.create())
        FundingFactory.create(review_status='open', image=ImageFactory.create())

        response = self.client.get(self.url, user=self.owner)

        for activity in response.json()['data']:
            self.assertTrue(
                re.match('^/api/activities/\d+/image/600x337', activity['attributes']['image'])
            )

    def test_deed_preview(self):
        activity = DeedFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], None)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)

    def test_date_preview(self):
        activity = DateActivityFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 1)
        self.assertEqual(dateutil.parser.parse(attributes['start']), activity.slots.first().start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), activity.slots.first().end)
        self.assertEqual(attributes['has-multiple-locations'], False)
        location = activity.slots.first().location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_multiple_slots(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(3, activity=activity)
        DateActivitySlotFactory.create(
            status='succeeded', activity=activity, start=now() - timedelta(days=10)
        )
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 3)
        self.assertEqual(
            dateutil.parser.parse(attributes['start']),
            min([slot.start for slot in activity.slots.all() if slot.start > now()])
        )

        self.assertEqual(
            dateutil.parser.parse(attributes['end']),
            min([slot.end for slot in activity.slots.all() if slot.start > now()])
        )
        self.assertEqual(attributes['has-multiple-locations'], True)
        self.assertIsNone(attributes['location'])

    def test_date_preview_multiple_slots_single_location(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        location = GeolocationFactory.create()
        DateActivitySlotFactory.create_batch(3, activity=activity, location=location)
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 3)
        self.assertEqual(attributes['has-multiple-locations'], False)

        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_multiple_slots_single_open(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create(activity=activity, status='draft', is_online=None)
        open_slot = DateActivitySlotFactory.create(activity=activity)

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slot-count'], 1)
        self.assertEqual(attributes['has-multiple-locations'], False)

        self.assertEqual(
            attributes['location'],
            f'{open_slot.location.locality}, {open_slot.location.country.alpha2_code}'
        )

        self.assertEqual(dateutil.parser.parse(attributes['start']), open_slot.start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), open_slot.end)

    def test_date_preview_multiple_slots_filtered(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=14))
        DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=21))
        current_slot = DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=7))

        start = now()
        end = start + timedelta(days=8)
        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
        )
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['slot-count'], 1)

        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(dateutil.parser.parse(attributes['start']), current_slot.start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), current_slot.end)

        location = current_slot.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_all_full(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(3, activity=activity, status='full')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['is-full'], True)

    def test_date_preview_is_online(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(
            3, activity=activity, location=None, is_online=True, status='full'
        )
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['is-online'], True)

    def test_date_preview_matching(self):
        activity = DateActivityFactory.create(
            status='open',
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        DateActivitySlotFactory.create(
            activity=activity
        )

        self.owner.favourite_themes.add(activity.initiative.theme)
        self.owner.skills.add(activity.expertise)
        self.owner.place = PlaceFactory.create(
            position=Point(20.0, 10.0)
        )
        self.owner.save()

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['matching-properties']['theme'], True)
        self.assertEqual(attributes['matching-properties']['skill'], True)
        self.assertEqual(attributes['matching-properties']['location'], True)

    def test_period_preview(self):
        activity = PeriodActivityFactory.create(status='open', is_online=False)
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['contribution-duration'], {'period': 'overall', 'value': 20.0})

        location = activity.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

        self.assertEqual(attributes['matching-properties']['theme'], False)
        self.assertEqual(attributes['matching-properties']['skill'], False)
        self.assertEqual(attributes['matching-properties']['location'], False)

    def test_period_preview_matching(self):
        activity = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        self.owner.favourite_themes.add(activity.initiative.theme)
        self.owner.skills.add(activity.expertise)
        self.owner.place = PlaceFactory.create(
            position=Point(20.0, 10.0)
        )
        self.owner.save()

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['matching-properties']['theme'], True)
        self.assertEqual(attributes['matching-properties']['skill'], True)
        self.assertEqual(attributes['matching-properties']['location'], True)

    def test_funding_preview(self):
        activity = FundingFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], None)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], None)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)

        location = activity.initiative.place
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_collect_preview(self):
        activity = CollectActivityFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], None)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.initiative.theme.name)
        self.assertEqual(attributes['expertise'], None)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['collect-type'], activity.collect_type.name)

        location = activity.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_collect_preview_dutch(self):
        activity = CollectActivityFactory.create(status='open')
        theme_translation = activity.initiative.theme.translations.get(
            language_code='nl'
        )

        collect_type_translation = activity.collect_type.translations.get(
            language_code='nl'
        )
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['theme'], theme_translation.name)
        self.assertEqual(attributes['collect-type'], collect_type_translation.name)

    def test_no_filter(self):
        succeeded = DateActivityFactory.create(
            owner=self.owner, status='succeeded'
        )
        open = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='submitted')
        DateActivityFactory.create(status='closed')
        DateActivityFactory.create(status='cancelled')
        DateActivityFactory.create(status='rejected')

        response = self.client.get(self.url, user=self.owner)
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], str(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], str(open.pk))

    def test_anonymous(self):
        succeeded = DateActivityFactory.create(
            owner=self.owner,
        )
        succeeded.initiative.states.submit(save=True)
        succeeded.initiative.states.approve(save=True)
        succeeded.states.submit(save=True)

        slot = succeeded.slots.get()
        slot.start = now() - timedelta(days=10)
        slot.save()

        DateParticipantFactory.create(
            activity=succeeded
        )

        open = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='submitted')
        DateActivityFactory.create(status='closed')

        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], str(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], str(open.pk))

    def setup_closed_segments(self):
        self.closed_segment = SegmentFactory.create(closed=True)
        self.open_segment = SegmentFactory.create()

        self.without_segment = DateActivityFactory.create(status='succeeded')

        self.with_open_segment = DateActivityFactory.create(status='succeeded')
        self.with_open_segment.segments.add(self.open_segment)

        self.with_closed_segment = DateActivityFactory.create(status='open')
        self.with_closed_segment.segments.add(self.closed_segment)

    def test_closed_segments_anonymous(self):
        self.setup_closed_segments()

        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(self.without_segment.pk))
        self.assertEqual(data['data'][1]['id'], str(self.with_open_segment.pk))

    def test_closed_segments_user(self):
        self.setup_closed_segments()

        user = BlueBottleUserFactory.create()
        user.segments.add(self.closed_segment)

        response = self.client.get(self.url, user=user)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(self.without_segment.pk))
        self.assertEqual(data['data'][1]['id'], str(self.with_open_segment.pk))
        self.assertEqual(data['data'][2]['id'], str(self.with_closed_segment.pk))

    def test_closed_segments_staff(self):
        self.setup_closed_segments()

        staff = BlueBottleUserFactory.create(is_staff=True)

        response = self.client.get(self.url, user=staff)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(self.without_segment.pk))
        self.assertEqual(data['data'][1]['id'], str(self.with_open_segment.pk))
        self.assertEqual(data['data'][2]['id'], str(self.with_closed_segment.pk))

    def test_filter_matching(self):
        theme = ThemeFactory.create()
        self.owner.favourite_themes.add(theme)

        skill = SkillFactory.create()
        self.owner.skills.add(skill)

        self.owner.location = LocationFactory.create(position=Point(20.0, 10.0))
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = DateActivityFactory.create(
            status='open',
            initiative=initiative,
        )
        DateActivitySlotFactory.create(
            activity=first,
            is_online=False
        )

        second = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            initiative=initiative,
            is_online=False
        )
        third = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            initiative=initiative,
            expertise=skill,
            is_online=False
        )

        fourth = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            is_online=False
        )

        fifth = PeriodActivityFactory.create(
            status='open',
            expertise=skill,
            is_online=False
        )

        PeriodActivityFactory.create(
            status='open',
        )

        PeriodActivityFactory.create(
            status='closed',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            initiative=initiative,
            expertise=skill,
            is_online=False
        )

        response = self.client.get(
            self.url + '?filter[matching]',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(
            set([str(first.pk), str(second.pk), str(third.pk), str(fourth.pk), str(fifth.pk)]),
            set(activity['id'] for activity in data['data'])
        )
        for activity in data['data']:
            self.assertTrue(
                any([activity['attributes']['matching-properties'].values()])
            )

    def test_filter_owner(self):
        owned = DateActivityFactory.create(owner=self.owner, status='open')
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_filter_initiative(self):
        activity = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='draft', initiative=activity.initiative)
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[initiative.id]={}'.format(activity.initiative.pk),
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(activity.pk))

    def test_filter_initiative_owner(self):
        activity = DateActivityFactory.create(status='open')
        draft_activity = DateActivityFactory.create(status='draft', initiative=activity.initiative)
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[initiative.id]={}'.format(activity.initiative.pk),
            user=activity.initiative.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

        ids = [resource['id'] for resource in data['data']]
        self.assertTrue(str(activity.pk) in ids)
        self.assertTrue(str(draft_activity.pk) in ids)

    def test_filter_initiative_activity_manager(self):
        activity = DateActivityFactory.create(status='open')
        draft_activity = DateActivityFactory.create(status='draft', initiative=activity.initiative)
        DateActivityFactory.create(status='open')

        activity_manager = BlueBottleUserFactory.create()
        activity.initiative.activity_managers.add(activity_manager)

        response = self.client.get(
            self.url + '?filter[initiative.id]={}'.format(activity.initiative.pk),
            user=activity_manager
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

        ids = [resource['id'] for resource in data['data']]
        self.assertTrue(str(activity.pk) in ids)
        self.assertTrue(str(draft_activity.pk) in ids)

    def test_filter_initiative_activity_owner(self):
        activity = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='draft', initiative=activity.initiative)
        owned_draft_activity = DateActivityFactory.create(
            status='draft', initiative=activity.initiative, owner=self.owner
        )

        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[initiative.id]={}'.format(activity.initiative.pk),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

        ids = [resource['id'] for resource in data['data']]
        self.assertTrue(str(activity.pk) in ids)
        self.assertTrue(str(owned_draft_activity.pk) in ids)

    def test_filter_type(self):
        DateActivityFactory.create(status='open')
        PeriodActivityFactory.create(status='open')
        FundingFactory.create(status='open')
        DeedFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[type]=funding',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['attributes']['type'], 'funding')

        response = self.client.get(
            self.url + '?filter[type]=deed',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['attributes']['type'], 'deed')

        response = self.client.get(
            self.url + '?filter[type]=time_based',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        types = set(resource['attributes']['type'] for resource in data['data'])
        self.assertEqual(
            types,
            {'date', 'period'}
        )

    def test_filter_expertise(self):
        skill = SkillFactory.create()

        first = DateActivityFactory.create(status='open', expertise=skill)
        second = PeriodActivityFactory.create(status='open', expertise=skill)
        PeriodActivityFactory.create(status='open')
        PeriodActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[expertise.id]={}'.format(skill.id),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        ids = [resource['id'] for resource in data['data']]
        self.assertTrue(str(first.pk) in ids)
        self.assertTrue(str(second.pk) in ids)

    def test_filter_expertise_empty(self):
        first = DateActivityFactory.create(status='open', expertise=None)
        second = PeriodActivityFactory.create(status='open', expertise=None)
        PeriodActivityFactory.create(status='open')
        PeriodActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[expertise.id]=__empty__',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        ids = [resource['id'] for resource in data['data']]
        self.assertTrue(str(first.pk) in ids)
        self.assertTrue(str(second.pk) in ids)

    def test_only_owner_permission(self):
        owned = DateActivityFactory.create(owner=self.owner, status='open')
        DateActivityFactory.create(status='open')

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_activity')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_activity')
        )

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)

        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_location_filter(self):
        location = LocationFactory.create()
        activity = DateActivityFactory.create(status='open', office_location=location)
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[location.id]={}'.format(location.pk),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(activity.pk))

    def test_activity_date_filter(self):
        next_month = now() + dateutil.relativedelta.relativedelta(months=1)
        after = now() + dateutil.relativedelta.relativedelta(months=2)

        event = DateActivityFactory.create(
            status='open', slots=[]
        )
        DateActivitySlotFactory.create(activity=event, start=next_month)
        event_after = DateActivityFactory.create(
            status='open', slots=[]
        )
        DateActivitySlotFactory.create(activity=event_after, start=after)

        assignment = PeriodActivityFactory.create(
            status='open',
            deadline=next_month.date()
        )
        PeriodActivityFactory.create(
            status='open',
            deadline=after.date()
        )

        # Feature is not dealing with time. Disabling timezone check for test
        funding = FundingFactory.create(
            status='open',
            deadline=next_month
        )
        FundingFactory.create(
            status='open',
            deadline=after
        )

        start = next_month - dateutil.relativedelta.relativedelta(weeks=2)
        end = next_month + dateutil.relativedelta.relativedelta(weeks=2)
        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 5)

        found = [item['id'] for item in data['data']]
        self.assertTrue(str(event.pk) in found)
        self.assertTrue(str(assignment.pk) in found)
        self.assertTrue(str(funding.pk) in found)

        start = after - dateutil.relativedelta.relativedelta(weeks=2)
        end = after + dateutil.relativedelta.relativedelta(weeks=2)

        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        found = [item['id'] for item in data['data']]
        self.assertTrue(str(event.pk) not in found)
        self.assertTrue(str(assignment.pk) not in found)
        self.assertTrue(str(funding.pk) not in found)

        start = next_month + dateutil.relativedelta.relativedelta(days=2)
        end = next_month - dateutil.relativedelta.relativedelta(days=2)
        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 0)

    def test_activity_date_filter_slots(self):
        first = DateActivityFactory.create(
            status='open', slots=[]
        )
        for days in (2, 4, 6):
            DateActivitySlotFactory.create(
                activity=first,
                start=now() + timedelta(days=days)
            )

        second = DateActivityFactory.create(
            status='open', slots=[]
        )
        for days in (6, 8, 10):
            DateActivitySlotFactory.create(
                activity=second,
                status='full',
                start=now() + timedelta(days=days)
            )

        third = DateActivityFactory.create(
            status='open', slots=[]
        )
        for days in (2, 4, 6):
            DateActivitySlotFactory.create(
                activity=third,
                status='cancelled',
                start=now() + timedelta(days=days)

            )
        start = (now() + timedelta(days=2)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=2)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertTrue(str(first.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=5)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertTrue(str(first.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=6)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertTrue(str(first.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(second.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=6)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=6)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertTrue(str(first.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(second.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=7)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=7)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 0)

        start = (now() + timedelta(days=8)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=10)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertTrue(str(second.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=12)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=30)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 0)

    def test_activity_date_filter_period(self):
        open_end = PeriodActivityFactory.create(
            status='open',
            start=date.today() + timedelta(days=5),
            deadline=None
        )

        open_start = PeriodActivityFactory.create(
            status='open',
            start=None,
            deadline=date.today() + timedelta(days=20)
        )

        first = PeriodActivityFactory.create(
            status='open',
            start=date.today() + timedelta(days=5),
            deadline=date.today() + timedelta(days=10)
        )

        second = PeriodActivityFactory.create(
            status='open',
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=15)
        )

        third = PeriodActivityFactory.create(
            status='open',
            start=date.today() + timedelta(days=15),
            deadline=date.today() + timedelta(days=20)
        )

        start = (now() + timedelta(days=5)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=5)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertTrue(str(first.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(open_start.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(open_end.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=14)).strftime('%Y-%m-%d')
        end = (now() + timedelta(days=18)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}&filter[end]={end}'.format(
                    start=start, end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 4)
        self.assertTrue(str(open_start.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(open_end.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(second.pk) in [item['id'] for item in data['data']])
        self.assertTrue(str(third.pk) in [item['id'] for item in data['data']])

        start = (now() + timedelta(days=25)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[start]={start}'.format(
                    start=start
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertTrue(str(open_end.pk) in [item['id'] for item in data['data']])

        end = (now() + timedelta(days=1)).strftime('%Y-%m-%d')
        data = json.loads(
            self.client.get(
                self.url + '?filter[end]={end}'.format(
                    end=end
                ),
                user=self.owner
            ).content
        )
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertTrue(str(open_start.pk) in [item['id'] for item in data['data']])

    def test_activity_invalid_date_filter(self):
        next_month = now() + dateutil.relativedelta.relativedelta(months=1)
        after = now() + dateutil.relativedelta.relativedelta(months=2)

        event = DateActivityFactory.create(
            status='open', slots=[]
        )
        DateActivitySlotFactory.create(activity=event, start=next_month)
        event_after = DateActivityFactory.create(
            status='open', slots=[]
        )
        DateActivitySlotFactory.create(activity=event_after, start=after)

        PeriodActivityFactory.create(
            status='open',
            deadline=next_month.date()
        )
        response = self.client.get(
            self.url + '?filter[start]=0'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            self.url + '?filter[end]=2021-02-31'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_segment(self):
        segment = SegmentFactory.create()
        first = DateActivityFactory.create(
            status='open',
        )
        first.segments.add(segment)

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[segment.{}]={}'.format(
                segment.segment_type.slug, segment.pk
            ),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

    def test_filter_upcoming(self):
        first = DateActivityFactory.create(
            status='open',
        )

        second = DateActivityFactory.create()
        second.status = 'full'
        second.save()

        succeeded = DateActivityFactory.create()
        succeeded.status = 'succeeded'
        succeeded.save()

        response = self.client.get(
            self.url + '?filter[upcoming]=true',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))

    def test_filter_upcoming_false(self):
        DateActivityFactory.create(
            status='open',
        )

        second = DateActivityFactory.create()
        second.status = 'full'
        second.save()

        succeeded = DateActivityFactory.create()
        succeeded.status = 'succeeded'
        succeeded.save()

        response = self.client.get(
            self.url + '?filter[upcoming]=false',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(succeeded.pk))

    def test_filter_segment_mismatch(self):
        first = DateActivityFactory.create(
            status='open',
        )
        first_segment = SegmentFactory.create()
        first.segments.add(first_segment)
        second_segment = SegmentFactory.create()
        first.segments.add(second_segment)

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[segment.{}]={}'.format(
                first_segment.segment_type.slug, second_segment.pk
            ),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 0)

    def test_filter_by_office(self):

        europe = OfficeRegionFactory.create(name='Europe')
        africa = OfficeRegionFactory.create(name='Africa')
        netherlands = OfficeSubRegionFactory.create(
            region=europe,
            name='The Netherlands'
        )
        bulgaria = OfficeSubRegionFactory.create(
            region=europe,
            name='Bulgaria'
        )
        namibia = OfficeSubRegionFactory.create(
            region=africa,
            name='Nambibia'
        )
        amsterdam = LocationFactory.create(name='Amsterdam', subregion=netherlands)
        leiden = LocationFactory.create(name='Leiden', subregion=netherlands)
        lyutidol = LocationFactory.create(name='Lyutidol', subregion=bulgaria)
        windhoek = LocationFactory.create(name='Windhoek', subregion=namibia)

        DateActivityFactory.create(
            office_location=leiden,
            status='open',
            office_restriction='office'
        )
        DateActivityFactory.create(
            office_location=amsterdam,
            status='open',
            office_restriction='office_subregion'
        )
        DateActivityFactory.create(
            office_location=amsterdam,
            status='open',
            office_restriction='office_subregion'
        )
        DateActivityFactory.create(
            office_location=lyutidol,
            status='open',
            office_restriction='office_region'
        )
        DateActivityFactory.create(
            office_location=windhoek,
            status='open',
            office_restriction='all'
        )
        DateActivityFactory.create(
            office_location=windhoek,
            status='open',
            office_restriction='office_region'
        )
        platform = InitiativePlatformSettings.load()
        platform.enable_office_restrictions = False
        platform.save()

        user = BlueBottleUserFactory.create()
        response = self.client.get(self.url, user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 6)

        response = self.client.get(f'{self.url}?filter[office]={windhoek.id}', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 6)

        platform = InitiativePlatformSettings.load()
        platform.enable_office_restrictions = True
        platform.save()

        user = BlueBottleUserFactory.create()
        response = self.client.get(self.url, user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 6)

        user = BlueBottleUserFactory.create()
        response = self.client.get(f'{self.url}?filter[office]={windhoek.id}', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

        response = self.client.get(f'{self.url}?filter[office]={leiden.id}', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 5)

        response = self.client.get(f'{self.url}?filter[office]={lyutidol.id}', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

        response = self.client.get(f'{self.url}?filter[office]={amsterdam.id}', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 4)

        response = self.client.get(f'{self.url}?filter[office]=false', user=user)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)

    def test_search(self):
        first = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            status='open'
        )
        second = DateActivityFactory.create(title='Lorem ipsum dolor sit amet', status='open')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))

    def test_search_team_activity(self):
        first = DateActivityFactory.create(
            team_activity='teams',
            status='open'
        )
        DateActivityFactory.create_batch(
            2,
            team_activity='individuals',
            status='open'
        )

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        response = self.client.get(
            self.url + '?filter[team_activity]=teams',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

        response = self.client.get(
            self.url + '?filter[team_activity]=individuals',
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_search_page_size(self):
        DateActivityFactory.create_batch(
            12,
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            status='open'
        )
        response = self.client.get(
            self.url + '?page[size]=4'
        )
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 12)
        self.assertEqual(len(data['data']), 4)

        response = self.client.get(
            self.url + '?page[size]=8'
        )
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 12)
        self.assertEqual(len(data['data']), 8)

        response = self.client.get(
            self.url
        )
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 12)
        self.assertEqual(len(data['data']), 8)

    def test_search_different_type(self):
        first = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            status='open'
        )
        second = PeriodActivityFactory.create(title='Lorem ipsum dolor sit amet', status='open')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][0]['type'], 'activities/preview')
        self.assertEqual(data['data'][0]['attributes']['type'], 'date')
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][0]['type'], 'activities/preview')
        self.assertEqual(data['data'][1]['attributes']['type'], 'period')

    def test_search_boost(self):
        first = DateActivityFactory.create(
            title='Something else',
            description='Lorem ipsum dolor sit amet',
            status='open'
        )
        second = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Something else",
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_formatted_address(self):
        activity1 = DateActivityFactory.create(
            title='Location! Location!',
            status='open'
        )
        location = GeolocationFactory.create(formatted_address='Roggeveenstraat')
        DateActivitySlotFactory.create(
            location=location,
            activity=activity1
        )
        DateActivitySlotFactory.create(
            activity=activity1,
            location=location)

        activity2 = DateActivityFactory.create(
            title='Nog een!',
            status='open'
        )
        DateActivitySlotFactory.create(
            location=location,
            activity=activity2
        )
        activity3 = DateActivityFactory.create(
            title='Nog een!',
            status='open'
        )
        DateActivitySlotFactory.create(
            activity=activity3
        )

        response = self.client.get(
            self.url + '?filter[search]=Roggeveenstraat',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(activity1.pk))
        self.assertEqual(data['data'][1]['id'], str(activity2.pk))

    def test_search_initiative_title(self):
        first = DateActivityFactory.create(
            initiative=InitiativeFactory.create(title='Test title'),
            status='open'
        )
        second = DateActivityFactory.create(
            title='Test title',
            status='open'
        )
        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=test title',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_segment_name(self):
        first = DateActivityFactory.create(
            status='open',
        )
        first.segments.add(SegmentFactory(name='Online Marketing'))

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=marketing',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

    def test_sort_title(self):
        second = DateActivityFactory.create(title='B: something else', status='open')
        first = DateActivityFactory.create(title='A: something', status='open')
        third = DateActivityFactory.create(title='C: More', status='open')

        response = self.client.get(
            self.url + '?sort=alphabetical',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))

    def test_sort_activity_date(self):
        first = DateActivityFactory.create(
            status='open',
        )
        DateActivitySlotFactory.create(
            activity=first,
            start=now() + timedelta(days=10)
        )

        second = FundingFactory.create(
            status='open',
            deadline=now() + timedelta(days=9)
        )

        third = PeriodActivityFactory.create(
            status='open',
            start=now() + timedelta(days=4),
            deadline=now() + timedelta(days=11)
        )

        response = self.client.get(
            self.url + '?sort=date',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))

    def test_sort_matching_status(self):
        DateActivityFactory.create(status='closed')

        second = DateActivityFactory.create(
            owner=self.owner,
        )
        second.initiative.states.submit(save=True)
        second.initiative.states.approve(save=True)
        second.states.submit(save=True)

        slot = second.slots.get()
        slot.start = now() - timedelta(days=10)
        slot.save()

        DateParticipantFactory.create(
            activity=second
        )

        third = DateActivityFactory.create(
            status='open',
            capacity=1
        )
        DateParticipantFactory.create(activity=third)
        fourth = DateActivityFactory.create(status='running')
        DateParticipantFactory.create(activity=fourth)
        fifth = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(activity=fifth)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(fifth.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))

    def test_sort_matching_activity_date(self):
        first = DateActivityFactory.create(
            status='open',
        )
        DateActivitySlotFactory.create(
            activity=first,
            start=now() + timedelta(days=10)
        )

        second = FundingFactory.create(
            status='open',
            deadline=now() + timedelta(days=9)
        )

        third = PeriodActivityFactory.create(
            status='open',
            start=now() + timedelta(days=4),
            deadline=now() + timedelta(days=11)
        )

        fourth = PeriodActivityFactory.create(
            status='open',
            deadline=None,
            start=None
        )

        response = self.client.get(
            self.url + '?sort=popularity'
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(fourth.pk))

    def test_sort_matching_skill(self):
        skill = SkillFactory.create()
        self.owner.skills.add(skill)
        self.owner.save()

        first = PeriodActivityFactory.create(status='full')

        second = PeriodActivityFactory.create(status='full', expertise=skill)

        third = PeriodActivityFactory.create(status='open')
        fourth = PeriodActivityFactory.create(status='open', expertise=skill)
        fifth = PeriodActivityFactory.create(status='open', expertise=None)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(fifth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))
        self.assertEqual(data['data'][4]['id'], str(first.pk))

    def test_sort_matching_theme(self):
        theme = ThemeFactory.create()
        self.owner.favourite_themes.add(theme)
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = DateActivityFactory.create(status='open', capacity=1)
        DateParticipantFactory.create(activity=first)
        second = DateActivityFactory.create(
            status='open',
            initiative=initiative,
            capacity=1
        )
        DateParticipantFactory.create(activity=second)
        third = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(activity=third)
        fourth = DateActivityFactory.create(status='open', initiative=initiative)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(third.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))
        self.assertEqual(data['data'][3]['id'], str(first.pk))

    def test_sort_matching_location(self):
        self.owner.place = PlaceFactory.create(
            position=Point(20.0, 10.0)
        )
        self.owner.save()

        first = PeriodActivityFactory.create(status='full')

        second = PeriodActivityFactory.create(
            status='full',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        third = PeriodActivityFactory.create(
            status='open',
            is_online=False,
        )
        fourth = PeriodActivityFactory.create(
            status='open',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        fifth = PeriodActivityFactory.create(
            is_online=True,
            status='open',
            location=None
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(fifth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))
        self.assertEqual(data['data'][4]['id'], str(first.pk))

    def test_sort_contribution_count(self):

        deadline = now() + timedelta(days=2)
        first = FundingFactory.create(status='open', deadline=deadline)
        deadline = now() + timedelta(days=10)
        second = FundingFactory.create(status='open', deadline=deadline)
        third = FundingFactory.create(status='open', deadline=deadline)
        fourth = FundingFactory.create(status='open', deadline=deadline)
        fifth = FundingFactory.create(status='open', deadline=deadline)

        DonorFactory.create_batch(10, activity=fourth, status='succeeded')
        DonorFactory.create_batch(5, activity=fifth, status='succeeded')
        DonorFactory.create_batch(3, activity=third, status='succeeded')

        response = self.client.get(
            self.url + '?sort=popularity'
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(fifth.pk))
        self.assertEqual(data['data'][3]['id'], str(third.pk))
        self.assertEqual(data['data'][4]['id'], str(second.pk))

    def test_facet_type(self):
        DateActivityFactory.create_batch(3, status='open')
        PeriodActivityFactory.create_batch(2, status='open')
        FundingFactory.create_batch(1, status='open')
        DeedFactory.create_batch(3, status='open')
        CollectActivityFactory.create_batch(4, status='open')

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = json.loads(response.content)
        facets = dict(
            (facet['value'], facet['count']) for facet in data['meta']['facets']['activity-type']
        )
        self.assertEqual(facets['time'], 5)
        self.assertEqual(facets['funding'], 1)
        self.assertEqual(facets['collect'], 4)
        self.assertEqual(facets['deed'], 3)

        self.assertEqual(data['meta']['pagination']['count'], 13)

    def test_facet_segment(self):
        segment_types = SegmentTypeFactory.create_batch(2, is_active=True, enable_search=True)

        for segment_type in segment_types:
            segments = SegmentFactory.create_batch(2, segment_type=segment_type)
            for segment in segments:
                date_activity = DateActivityFactory.create(status='open')
                date_activity.segments.add(segment)

                collect_activity = CollectActivityFactory.create(status='open')
                collect_activity.segments.add(segment)

        selected_segment = segment_types[0].segments.first()
        response = self.client.get(
            f'{self.url}?filter[segment.{selected_segment.segment_type.slug}]={selected_segment.pk}',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(
            set(activity['id'] for activity in data['data']),
            set(str(activity.pk) for activity in selected_segment.activities.all())
        )

        for segment_type in segment_types:
            if segment_type == selected_segment.segment_type:
                for segment in segment_type.segments.all():
                    self.assertTrue(
                        {
                            'name': segment.name,
                            'id': str(segment.pk),
                            'count': 2,
                            'active': segment == selected_segment
                        } in data['meta']['facets'][f'segment.{segment_type.slug}']
                    )
            else:
                self.assertEqual(data['meta']['facets'][f'segment.{segment_type.slug}'], [])

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_facet_theme(self):
        initiatives = InitiativeFactory.create_batch(4, status='approved')
        for initiative in initiatives:
            DateActivityFactory.create_batch(2, status='open', initiative=initiative)
            PeriodActivityFactory.create_batch(3, status='open', initiative=initiative)
            CollectActivityFactory.create_batch(4, status='open', initiative=initiative)
            DeedFactory.create_batch(3, status='open', initiative=initiative)
            FundingFactory.create_batch(1, status='open', initiative=initiative)

        response = self.client.get(
            f'{self.url}?filter[theme]={initiatives[0].theme.pk}',
            user=self.owner
        )

        data = json.loads(response.content)
        types = dict(
            (facet['id'], facet['count']) for facet in data['meta']['facets']['activity-type']
        )
        self.assertEqual(types['time'], 5)
        self.assertEqual(types['funding'], 1)
        self.assertEqual(types['collect'], 4)
        self.assertEqual(types['deed'], 3)

        for initiative in initiatives[1:]:
            self.assertTrue(
                {
                    'name': initiative.theme.name,
                    'id': str(initiative.theme.pk),
                    'count': 13,
                    'active': False
                } in data['meta']['facets']['theme']
            )

        self.assertTrue(
            {
                'name': initiatives[0].theme.name,
                'id': str(initiatives[0].theme.pk),
                'count': 13,
                'active': True
            } in data['meta']['facets']['theme']
        )

        self.assertEqual(data['meta']['pagination']['count'], 13)

    def test_filter_country(self):
        country1 = CountryFactory.create()
        country2 = CountryFactory.create()

        initiative1 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative2 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))
        initiative3 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative4 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))

        location1 = GeolocationFactory(country=country1)
        location2 = GeolocationFactory(country=country2)

        first = PeriodActivityFactory.create(status='full', initiative=initiative1, location=location1)
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(status='open', initiative=initiative3, location=location1)

        third = PeriodActivityFactory.create(status='full', initiative=initiative2, location=location2)
        PeriodParticipantFactory.create_batch(3, activity=third, status='accepted')

        PeriodActivityFactory.create(status='open', initiative=initiative4)

        response = self.client.get(
            self.url + '?sort=popularity&filter[country]={}'.format(country1.id),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_filter_office_country(self):
        country1 = CountryFactory.create()
        country2 = CountryFactory.create()
        office1 = LocationFactory.create(country=country1)
        office2 = LocationFactory.create(country=country2)

        location1 = GeolocationFactory(country=country1)

        first = PeriodActivityFactory.create(status='full', office_location=office1, is_online=True)
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(status='open', office_location=office1, is_online=True)

        third = PeriodActivityFactory.create(status='full', office_location=office2, location=location1)
        PeriodParticipantFactory.create_batch(3, activity=third, status='accepted')

        PeriodActivityFactory.create(status='open', office_location=office2, is_online=True)
        date = DateActivityFactory.create(status='open', office_location=office1)
        DateActivitySlotFactory.create(activity=date, status='open', is_online=True)

        response = self.client.get(
            self.url + '?sort=popularity&filter[country]={}'.format(country1.id),
            user=self.owner
        )

        data = json.loads(response.content)
        # Country filter should activities with initiative with office with that country,
        # but also activities with a (geo)location in that country
        self.assertEqual(data['meta']['pagination']['count'], 4)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(date.pk))
        self.assertEqual(data['data'][2]['id'], str(first.pk))

    def test_filter_mixed_country(self):
        country1 = CountryFactory.create()
        office1 = LocationFactory.create(country=country1)
        location1 = GeolocationFactory(country=country1)

        initiative1 = InitiativeFactory.create(place=None)
        initiative2 = InitiativeFactory.create(place=None)
        initiative3 = InitiativeFactory.create(place=None)
        initiative4 = InitiativeFactory.create(place=location1)

        PeriodActivityFactory.create(status='full', initiative=initiative1, is_online=True)
        date1 = DateActivityFactory.create(status='open', initiative=initiative2)
        date2 = DateActivityFactory.create(status='open', initiative=initiative3, office_location=office1)
        PeriodActivityFactory.create(status='full', initiative=initiative4, is_online=True)

        DateActivitySlotFactory.create(activity=date1, status='open', is_online=False, location=location1)
        DateActivitySlotFactory.create(activity=date2, status='open', is_online=True)

        response = self.client.get(
            self.url + '?sort=popularity&filter[country]={}'.format(country1.id),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

    def test_sort_matching_office_location(self):
        self.owner.location = LocationFactory.create(position=Point(20.0, 10.0))
        self.owner.save()

        first = PeriodActivityFactory.create(status='full')

        second = PeriodActivityFactory.create(
            status='full',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        third = PeriodActivityFactory.create(status='open')
        fourth = PeriodActivityFactory.create(
            status='open',
            is_online=True,
        )
        fifth = PeriodActivityFactory.create(
            status='open',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], str(fifth.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))
        self.assertEqual(data['data'][4]['id'], str(first.pk))

    def test_sort_matching_combined(self):
        theme = ThemeFactory.create()
        self.owner.favourite_themes.add(theme)

        skill = SkillFactory.create()
        self.owner.skills.add(skill)

        self.owner.location = LocationFactory.create(position=Point(20.0, 10.0))
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = DateActivityFactory.create(
            status='open',
            initiative=initiative,
        )
        DateActivitySlotFactory.create(
            activity=first,
            is_online=False
        )

        second = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            initiative=initiative,
            is_online=False
        )
        third = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1)),
            initiative=initiative,
            expertise=skill,
            is_online=False
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(first.pk))

    def test_limits(self):
        initiative = InitiativeFactory.create()
        DateActivityFactory.create_batch(
            7,
            status='open',
            initiative=initiative,
        )
        response = self.client.get(
            self.url + '?page[size]=150',
            user=self.owner
        )
        self.assertEqual(len(response.json()['data']), 7)

        response = self.client.get(
            self.url + '?page[size]=3',
            user=self.owner
        )
        self.assertEqual(len(response.json()['data']), 3)


class ActivityRelatedImageAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ActivityRelatedImageAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.funding = FundingFactory.create(
            owner=self.owner,
        )
        self.related_image_url = reverse('related-activity-image-list')

        file_path = './bluebottle/files/tests/files/test-image.png'

        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                format=None,
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
                user=self.owner
            )

        self.file_data = json.loads(response.content)

    def test_create(self):
        data = {
            'data': {
                'type': 'related-activity-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.related_image_url,
            data=json.dumps(data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['included'][1]['attributes']['links']['large'].split('?')[0],
            u'/api/activities/{}/related-image/600'.format(response.json()['data']['id'])
        )

    def test_create_non_owner(self):
        data = {
            'data': {
                'type': 'related-activity-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.related_image_url,
            data=json.dumps(data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ContributorListAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ContributorListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        participants = DateParticipantFactory.create_batch(2, user=self.user)
        for participant in participants:
            slot = DateActivitySlotFactory.create(activity=participant.activity)
            slot.slot_participants.all()[0].states.remove(save=True)

        PeriodParticipantFactory.create_batch(2, user=self.user)
        DonorFactory.create_batch(2, user=self.user, status='succeeded')
        DonorFactory.create_batch(2, user=self.user, status='new')
        DeedParticipantFactory.create_batch(2, user=self.user)
        CollectContributorFactory.create_batch(2, user=self.user)

        DateParticipantFactory.create()
        PeriodParticipantFactory.create()
        DonorFactory.create()
        DeedParticipantFactory.create()
        CollectContributorFactory.create()

        self.url = reverse('contributor-list')

    def test_get(self):
        response = self.client.get(
            self.url,
            user=self.user
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 10)

        for contributor in data['data']:
            self.assertTrue(
                contributor['type'] in (
                    'contributors/time-based/date-participants',
                    'contributors/time-based/period-participants',
                    'contributors/collect/contributors',
                    'contributors/deeds/participant',
                    'contributors/donations',
                )
            )
            self.assertTrue(contributor['type'])
            self.assertTrue(
                contributor['relationships']['activity']['data']['type'] in (
                    'activities/fundings',
                    'activities/deeds',
                    'activities/time-based/dates',
                    'activities/time-based/periods',
                    'activities/collects'
                )
            )

            if contributor['type'] == 'contributors/time-based/date-participants':
                self.assertEqual(contributor['attributes']['total-duration'], '02:00:00')

        self.assertEqual(
            len([
                resource for resource in data['included']
                if resource['type'] == 'activities/time-based/periods'
            ]),
            2
        )

        self.assertEqual(
            len([
                resource for resource in data['included']
                if resource['type'] == 'activities/time-based/dates'
            ]),
            2
        )

        self.assertEqual(
            len([
                resource for resource in data['included']
                if resource['type'] == 'activities/deeds'
            ]),
            2
        )

        self.assertEqual(
            len([
                resource for resource in data['included']
                if resource['type'] == 'activities/fundings'
            ]),
            2
        )

    def test_get_anonymous(self):
        response = self.client.get(
            self.url
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 0)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityAPIAnonymizationTestCase(ESTestCase, BluebottleTestCase):
    anonymous_resource = {
        'id': 'anonymous',
        'type': 'members',
        'attributes': {
            'is-anonymous': True
        }
    }

    def setUp(self):
        super(ActivityAPIAnonymizationTestCase, self).setUp()
        self.member_settings = MemberPlatformSettings.load()

        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()

    def test_activity_over_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()

        activity = DateActivityFactory.create(
            created=now() - timedelta(days=400),
            status='open'
        )

        data = self.client.get(
            reverse('date-detail', args=(activity.id,))
        ).json()

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'], 'anonymous'
        )

        self.assertTrue(self.anonymous_resource in data['included'])

    def test_activity_not_over_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()

        activity = DateActivityFactory.create(
            created=now() - timedelta(days=200),
            status='open'
        )

        data = self.client.get(
            reverse('date-detail', args=(activity.id,))
        ).json()

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'], str(activity.owner.pk)
        )

        self.assertTrue(self.anonymous_resource not in data['included'])

    def test_initiative_over_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()

        initiative = InitiativeFactory.create(
            status='open',
            promoter=BlueBottleUserFactory.create(),
            reviewer=BlueBottleUserFactory.create(),
        )

        initiative.created = now() - timedelta(days=400)
        initiative.save()

        DateActivityFactory.create(
            initiative=initiative,
            created=now() - timedelta(days=400),
            status='open'
        )
        data = self.client.get(
            reverse('initiative-detail', args=(initiative.id,))
        ).json()

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'], 'anonymous'
        )

        self.assertEqual(
            data['data']['relationships']['activity-managers']['data'][0]['id'], 'anonymous'
        )

        self.assertEqual(
            data['data']['relationships']['reviewer']['data']['id'], 'anonymous'
        )

    def test_initiative_not_over_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()

        initiative = InitiativeFactory.create(
            status='open',
            promoter=BlueBottleUserFactory.create(),
            reviewer=BlueBottleUserFactory.create(),
        )

        initiative.created = now() - timedelta(days=200)
        initiative.save()

        DateActivityFactory.create(
            initiative=initiative,
            status='open'
        )
        data = self.client.get(
            reverse('initiative-detail', args=(initiative.id,))
        ).json()

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'], str(initiative.owner.pk)
        )

        self.assertEqual(
            data['data']['relationships']['activity-managers']['data'][0]['id'],
            str(initiative.activity_managers.first().pk)
        )

        self.assertEqual(
            data['data']['relationships']['reviewer']['data']['id'], str(initiative.reviewer.pk)
        )

    def test_participants_over_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()

        activity = DateActivityFactory.create(
            created=now() - timedelta(days=400),
            status='open'
        )

        activity_data = self.client.get(
            reverse('date-detail', args=(activity.id,))
        ).json()

        DateParticipantFactory.create(
            activity=activity,
            created=now() - timedelta(days=350),
        )
        new_participant = DateParticipantFactory.create(
            activity=activity
        )

        data = self.client.get(
            activity_data['data']['relationships']['contributors']['links']['related'],
            user=self.owner
        ).json()
        self.assertEqual(
            data['data'][1]['relationships']['user']['data']['id'],
            'anonymous'
        )
        self.assertEqual(
            data['data'][0]['relationships']['user']['data']['id'],
            str(new_participant.user.pk)
        )


class TeamListViewAPITestCase(APITestCase):
    serializer = TeamSerializer

    def setUp(self):
        super().setUp()

        self.activity = PeriodActivityFactory.create(status='open')

        self.approved_teams = TeamFactory.create_batch(5, activity=self.activity)
        for team in self.approved_teams:
            PeriodParticipantFactory.create(activity=self.activity, team=team, user=team.owner)

        for team in self.approved_teams[:2]:
            TeamSlotFactory.create(activity=self.activity, team=team, start=now() + timedelta(days=5))

        TeamSlotFactory.create(
            activity=self.activity, team=self.approved_teams[2], start=now() - timedelta(days=5)
        )

        self.cancelled_teams = TeamFactory.create_batch(
            5, activity=self.activity, status='cancelled'
        )
        for team in self.cancelled_teams:
            PeriodParticipantFactory.create(activity=self.activity, team=team, user=team.owner)
            PeriodParticipantFactory.create(activity=self.activity, team=team)

        self.url = "{}?filter[activity_id]={}".format(
            reverse('team-list'),
            self.activity.pk
        )

        settings = InitiativePlatformSettings.objects.get()
        settings.team_activities = True
        settings.enable_participant_exports = True
        settings.save()

    def test_get_activity_owner(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.approved_teams) + len(self.cancelled_teams))
        self.assertObjectList(self.approved_teams)
        self.assertRelationship('owner')

        self.assertMeta('status')
        self.assertMeta('transitions')
        for resource in self.response.json()['data']:
            self.assertTrue(resource['meta']['participants-export-url'] is not None)
        team_ids = [t["id"] for t in self.response.json()["data"]]
        self.assertEqual(
            len(team_ids),
            len(set(team_ids)),
            'We should have a unique list of team ids'
        )

    def test_get_filtered_status(self):
        new_teams = TeamFactory.create_batch(2, activity=self.activity, status='new')
        self.perform_get(user=self.activity.owner, query={'filter[status]': 'new'})

        self.assertStatus(status.HTTP_200_OK)
        for resource in self.response.json()['data']:
            self.assertTrue(
                resource['id'] in [str(team.pk) for team in new_teams]
            )

    def test_get_filtered_has_no_slot(self):
        self.perform_get(user=self.activity.owner, query={'filter[has_slot]': 'false'})

        self.assertStatus(status.HTTP_200_OK)
        for resource in self.response.json()['data']:
            self.assertIsNone(resource['relationships']['slot']['data'])

    def test_get_filtered_future(self):
        self.perform_get(user=self.activity.owner, query={'filter[start]': 'future'})

        self.assertStatus(status.HTTP_200_OK)
        for resource in self.response.json()['data']:
            self.assertTrue(
                resource['id'] in [str(team.pk) for team in self.approved_teams[:2]]
            )

    def test_get_filtered_passed(self):
        self.perform_get(user=self.activity.owner, query={'filter[start]': 'passed'})

        self.assertStatus(status.HTTP_200_OK)
        for resource in self.response.json()['data']:
            self.assertEqual(
                resource['id'], str(self.approved_teams[2].pk)
            )

    def test_get_cancelled_team_captain(self):
        team = self.cancelled_teams[0]
        self.perform_get(user=team.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(len(self.approved_teams) + 1)
        self.assertObjectList(self.approved_teams + [team])
        self.assertRelationship('owner')

        self.assertEqual(
            self.response.json()['data'][0]['relationships']['owner']['data']['id'],
            str(team.owner.pk)
        )

    def test_get_team_captain(self):
        team = self.approved_teams[0]
        self.perform_get(user=team.owner)

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.approved_teams))
        self.assertObjectList(self.approved_teams)
        self.assertRelationship('owner')

        self.assertEqual(
            self.response.json()['data'][0]['relationships']['owner']['data']['id'],
            str(team.owner.pk)
        )

        for resource in self.response.json()['data']:
            if resource['relationships']['owner']['data']['id'] == str(team.owner.pk):
                self.assertTrue(resource['meta']['participants-export-url'] is not None)
            else:
                self.assertTrue(resource['meta']['participants-export-url'] is None)

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.approved_teams))
        self.assertObjectList(self.approved_teams)
        self.assertRelationship('owner')
        for resource in self.response.json()['data']:
            self.assertTrue(resource['meta']['participants-export-url'] is None)

    def test_pagination(self):
        extra_teams = TeamFactory.create_batch(
            10, activity=self.activity
        )
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.approved_teams) + len(extra_teams))
        self.assertSize(8)
        self.assertPages(2)

    def test_other_user_anonymous(self):
        self.perform_get(BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.approved_teams))
        self.assertObjectList(self.approved_teams)
        self.assertRelationship('owner')

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_user_closed_site(self):
        with self.closed_site():
            self.perform_get(BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)


class TeamTransitionListViewAPITestCase(APITestCase):
    url = reverse('team-transition-list')
    serializer = TeamTransitionSerializer

    def setUp(self):
        super().setUp()

        self.team = TeamFactory.create()

        self.defaults = {
            'resource': self.team,
            'transition': 'cancel',
        }

        self.fields = ['resource', 'transition', ]

    def test_cancel_owner(self):
        self.perform_create(user=self.team.owner)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'open')

    def test_cancel_activity_manager(self):
        self.perform_create(user=self.team.activity.owner)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.team)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'cancelled')

    def test_cancel_other_user(self):
        self.perform_create(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'open')

    def test_cancel_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'open')

    def test_withdraw_owner(self):
        self.defaults['transition'] = 'withdraw'

        self.perform_create(user=self.team.owner)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.team)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'withdrawn')

    def test_withdraw_activity_manager(self):
        self.defaults['transition'] = 'withdraw'

        self.perform_create(user=self.team.activity.owner)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.team.refresh_from_db()

        self.assertEqual(self.team.status, 'open')

    def test_withdraw_other_user(self):
        self.defaults['transition'] = 'withdraw'

        self.perform_create(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'open')

    def test_withdraw_no_user(self):
        self.defaults['transition'] = 'withdraw'

        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.team.refresh_from_db()
        self.assertEqual(self.team.status, 'open')


class InviteDetailViewAPITestCase(APITestCase):
    serializer = InviteSerializer

    def setUp(self):
        super().setUp()
        activity = PeriodActivityFactory.create(status='open', team_activity='teams')
        self.contributor = PeriodParticipantFactory.create(activity=activity)

        self.url = reverse('invite-detail', args=(self.contributor.invite.pk, ))

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('team', self.contributor.team)
        self.assertIncluded('team.owner', self.contributor.team.owner)

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_anonymous_user(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)


class TeamMemberExportViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        settings = InitiativePlatformSettings.load()
        settings.team_activities = True
        settings.enable_participant_exports = True
        settings.save()

        self.activity = PeriodActivityFactory.create(team_activity='teams')

        self.team_captain = PeriodParticipantFactory(activity=self.activity)

        self.team_members = PeriodParticipantFactory.create_batch(
            3,
            activity=self.activity,
            accepted_invite=self.team_captain.invite
        )

        self.non_team_members = PeriodParticipantFactory.create_batch(
            3,
            activity=self.activity,
        )

        self.url = "{}?filter[activity_id]={}".format(reverse('team-list'), self.activity.pk)

    @property
    def export_url(self):
        for team in self.response.json()['data']:
            if team['id'] == str(self.team_captain.team.pk) and team['meta']['participants-export-url']:
                return team['meta']['participants-export-url']['url']

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTrue(self.export_url)
        response = self.client.get(self.export_url)

        sheet = load_workbook(filename=io.BytesIO(response.content)).get_active_sheet()
        rows = list(sheet.values)

        self.assertEqual(
            rows[0],
            ('Email', 'Name', 'Registration Date', 'Status', 'Team Captain')
        )

        self.assertEqual(len(rows), 5)

        for team_member in self.team_members:
            self.assertTrue(team_member.user.email in [row[0] for row in rows[1:]])

        self.assertEqual(
            [
                row[4] for row in rows
                if row[0] == self.team_captain.user.email
            ][0],
            True
        )

    def test_team_captain(self):
        self.perform_get(user=self.team_captain.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTrue(self.export_url)
        response = self.client.get(self.export_url)
        sheet = load_workbook(filename=io.BytesIO(response.content)).get_active_sheet()
        rows = list(sheet.values)

        self.assertEqual(
            rows[0],
            ('Email', 'Name', 'Registration Date', 'Status', 'Team Captain')
        )

    def test_get_owner_incorrect_hash(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url + 'test')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_contributor(self):
        self.perform_get(user=self.team_members[0].user)
        self.assertIsNone(self.export_url)

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())
        self.assertIsNone(self.export_url)

    def test_get_no_user(self):
        self.perform_get()
        self.assertIsNone(self.export_url)


class TeamMemberListViewAPITestCase(APITestCase):
    serializer = PeriodParticipantSerializer

    def setUp(self):
        super().setUp()

        settings = InitiativePlatformSettings.objects.get()
        settings.team_activities = True
        settings.save()

        self.activity = PeriodActivityFactory.create(status='open', team_activity='teams')

        self.team_captain = PeriodParticipantFactory.create(
            activity=self.activity
        )
        self.team = self.team_captain.team

        self.accepted_members = PeriodParticipantFactory.create_batch(
            3,
            activity=self.activity,
            accepted_invite=self.team_captain.invite
        )
        self.withdrawn_members = PeriodParticipantFactory.create_batch(
            3,
            activity=self.activity,
            accepted_invite=self.team_captain.invite
        )

        for member in self.withdrawn_members:
            member.states.withdraw(save=True)

        self.url = reverse('team-members', args=(self.team.pk, ))

    def test_get_activity_owner(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.accepted_members) + len(self.withdrawn_members) + 1)
        self.assertRelationship('user')

        self.assertAttribute('status')
        self.assertMeta('transitions')

    def test_get_team_captain(self):
        self.perform_get(user=self.team.owner)

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.accepted_members) + len(self.withdrawn_members) + 1)
        ids = [m.id for m in self.accepted_members] + [m.id for m in self.withdrawn_members]

        self.assertEqual(len(set(ids)), 6)
        self.assertObjectList(self.accepted_members + self.withdrawn_members + [self.team_captain])
        self.assertRelationship('user')

        self.assertAttribute('status')
        self.assertMeta('transitions')

        self.assertTrue(
            str(self.team.owner.pk) in
            [m['relationships']['user']['data']['id'] for m in self.response.json()['data']]
        )

    def test_get_team_member(self):
        self.perform_get(user=self.accepted_members[0].user)

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.accepted_members) + 1)

        self.assertObjectList(self.accepted_members + [self.team_captain])
        self.assertRelationship('user')

        self.assertAttribute('status')
        self.assertMeta('transitions')

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.accepted_members) + 1)

        self.assertObjectList(self.accepted_members + [self.team_captain])
        self.assertRelationship('user')

        self.assertAttribute('status')
        self.assertMeta('transitions')

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class ActivityLocationAPITestCase(APITestCase):
    model = Activity

    def setUp(self):
        CollectActivityFactory.create(status='succeeded')
        PeriodActivityFactory.create(status='succeeded')

        date_activity = DateActivityFactory.create(status="succeeded")
        date_activity.slots.add(DateActivitySlotFactory.create(activity=date_activity))

        self.url = reverse('activity-location-list')

    def test_get(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(4)
        self.assertAttribute('position')
        self.assertRelationship('activity')

    def test_get_closed_platform(self):
        with self.closed_site():
            self.perform_get()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_platform_logged_in(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_200_OK)
