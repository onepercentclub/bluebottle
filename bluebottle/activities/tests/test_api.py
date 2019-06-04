import datetime
import json

from django.urls import reverse
from django.test import tag
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone, now

from django_elasticsearch_dsl.test import ESTestCase
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityListSearchAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ActivityListSearchAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.url = reverse('activity-list')

        self.user = BlueBottleUserFactory()

        self.url = reverse('activity-list')
        self.owner = BlueBottleUserFactory.create()

    def test_no_filter(self):
        EventFactory.create(owner=self.owner)
        EventFactory.create()

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_filter_owner(self):
        EventFactory.create(owner=self.owner)
        EventFactory.create()

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], unicode(self.owner.pk))

    def test_search(self):
        first = EventFactory.create(title='Lorem ipsum dolor sit amet', description="Lorem ipsum")
        second = EventFactory.create(title='Lorem ipsum dolor sit amet')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))

    def test_search_different_type(self):
        first = EventFactory.create(title='Lorem ipsum dolor sit amet', description="Lorem ipsum")
        second = FundingFactory.create(title='Lorem ipsum dolor sit amet')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][0]['type'], 'activities/events')
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['type'], 'activities/funding')

    def test_search_boost(self):
        first = EventFactory.create(title='Something else', description='Lorem ipsum dolor sit amet')
        second = EventFactory.create(title='Lorem ipsum dolor sit amet', description="Something else")

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_sort_title(self):
        second = EventFactory.create(title='B: something else')
        first = EventFactory.create(title='A: something')
        third = EventFactory.create(title='C: More')

        response = self.client.get(
            self.url + '?sort=alphabetical',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][2]['id'], unicode(third.pk))

    def test_sort_created(self):
        first = EventFactory.create()
        second = EventFactory.create()
        third = EventFactory.create()

        first.created = datetime.datetime(2018, 5, 8, tzinfo=get_current_timezone())
        first.save()
        second.created = datetime.datetime(2018, 5, 7, tzinfo=get_current_timezone())
        second.save()
        third.created = datetime.datetime(2018, 5, 9, tzinfo=get_current_timezone())
        third.save()

        response = self.client.get(
            self.url + '?sort=date',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], unicode(third.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))

    def test_sort_popularity(self):
        first = EventFactory.create()

        second = EventFactory.create()
        ParticipantFactory.create(
            activity=second, created=now() - datetime.timedelta(days=7)
        )

        third = EventFactory.create()
        ParticipantFactory.create(
            activity=third, created=now() - datetime.timedelta(days=5)
        )

        fourth = EventFactory.create()
        ParticipantFactory.create(
            activity=fourth, created=now() - datetime.timedelta(days=7)
        )
        ParticipantFactory.create(
            activity=fourth, created=now() - datetime.timedelta(days=5)
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(third.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))
        self.assertEqual(data['data'][3]['id'], unicode(first.pk))
