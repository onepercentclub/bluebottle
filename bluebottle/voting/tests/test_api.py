from django.urls import reverse
from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.voting.models import PollVote
from bluebottle.voting.serializers import PollSerializer, PollVoteSerializer
from bluebottle.voting.tests.factories import (
    PollFactory, PollOptionFactory, PollVoteFactory
)


class PollDetailAPITestCase(APITestCase):
    serializer = PollSerializer

    def setUp(self):
        super().setUp()
        self.poll = PollFactory.create(status='open', title='Favourite colour')
        self.option = PollOptionFactory.create(poll=self.poll, title='Blue')
        self.url = reverse('poll-detail', args=(self.poll.pk,))

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('title', 'Favourite colour')
        self.assertEqual(
            self.response.json()['data']['attributes']['votes-cast'],
            0
        )
        self.assertRelationship('options', [self.option])
        self.assertRelationship('my-vote')
        self.assertEqual(
            self.response.json()['data']['relationships']['my-vote']['data'],
            None
        )

    def test_get_with_votes(self):
        PollVoteFactory.create(poll=self.poll, option=self.option)
        PollVoteFactory.create(poll=self.poll, option=self.option)
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('votes_cast', 2)

    def test_get_authenticated_includes_my_vote(self):
        vote = PollVoteFactory.create(
            poll=self.poll, option=self.option, owner=self.user
        )
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('votes_cast', 1)
        self.assertRelationship('my-vote', [vote])
        self.assertIncluded('my-vote', vote)

    def test_get_authenticated_without_vote(self):
        PollVoteFactory.create(poll=self.poll, option=self.option)
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(
            self.response.json()['data']['relationships']['my-vote']['data'],
            None
        )

    def test_get_closed_poll(self):
        self.poll.status = 'closed'
        self.poll.save()
        self.perform_get()
        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_get_without_translation_in_request_language(self):
        self.response = self.client.get(
            self.url,
            HTTP_X_APPLICATION_LANGUAGE='nl'
        )
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('title', 'Favourite colour')


class PollVoteListAPITestCase(APITestCase):
    serializer = PollVoteSerializer
    factory = PollVoteFactory
    fields = ['poll', 'option']

    def setUp(self):
        super().setUp()
        self.poll = PollFactory.create(status='open')
        self.option = PollOptionFactory.create(poll=self.poll)
        self.other_option = PollOptionFactory.create(poll=self.poll)
        self.defaults = {
            'poll': self.poll,
            'option': self.option,
        }
        self.url = reverse('poll-vote-list')

    def test_create(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertRelationship('poll', [self.poll])
        self.assertRelationship('option', [self.option])
        self.assertEqual(PollVote.objects.filter(owner=self.user).count(), 1)

    def test_create_anonymous(self):
        self.perform_create()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_create_duplicate(self):
        PollVoteFactory.create(
            poll=self.poll, option=self.option, owner=self.user
        )
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PollVote.objects.filter(owner=self.user).count(), 1)

    def test_create_option_from_other_poll(self):
        other_poll = PollFactory.create(status='open')
        other_option = PollOptionFactory.create(poll=other_poll)
        self.defaults['option'] = other_option
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_closed_poll(self):
        self.poll.status = 'closed'
        self.poll.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)


class PollVoteDetailAPITestCase(APITestCase):
    serializer = PollVoteSerializer
    factory = PollVoteFactory

    def setUp(self):
        super().setUp()
        self.poll = PollFactory.create(status='open')
        self.option = PollOptionFactory.create(poll=self.poll)
        self.other_option = PollOptionFactory.create(poll=self.poll)
        self.model = PollVoteFactory.create(
            poll=self.poll, option=self.option, owner=self.user
        )
        self.url = reverse('poll-vote-detail', args=(self.model.pk,))

    def test_update_option(self):
        self.perform_update(
            to_change={'option': self.other_option},
            user=self.user
        )
        self.assertStatus(status.HTTP_200_OK)
        self.assertRelationship('option', [self.other_option])
        self.assertEqual(PollVote.objects.filter(owner=self.user).count(), 1)

    def test_update_anonymous(self):
        self.perform_update(to_change={'option': self.other_option})
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_update_other_user(self):
        other = BlueBottleUserFactory.create()
        self.perform_update(
            to_change={'option': self.other_option},
            user=other
        )
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_update_option_from_other_poll(self):
        other_option = PollOptionFactory.create()
        self.perform_update(
            to_change={'option': other_option},
            user=self.user
        )
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_update_closed_poll(self):
        self.poll.status = 'closed'
        self.poll.save()
        self.perform_update(
            to_change={'option': self.other_option},
            user=self.user
        )
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        self.perform_delete(user=self.user)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(PollVote.objects.filter(pk=self.model.pk).exists())

    def test_delete_anonymous(self):
        self.perform_delete()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_delete_other_user(self):
        other = BlueBottleUserFactory.create()
        self.perform_delete(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_delete_closed_poll(self):
        self.poll.status = 'closed'
        self.poll.save()
        self.perform_delete(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PollVote.objects.filter(pk=self.model.pk).exists())
