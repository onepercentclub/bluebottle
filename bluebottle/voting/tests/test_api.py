import io

from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.initiatives.models import InitiativePlatformSettings
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
        other = PollOptionFactory.create(poll=self.poll, title='Green')
        PollVoteFactory.create(poll=self.poll, option=self.option)
        PollVoteFactory.create(poll=self.poll, option=self.option)
        PollVoteFactory.create(poll=self.poll, option=other)
        self.poll.status = 'closed'
        self.poll.save()
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('status', 'closed')
        self.assertAttribute('votes_cast', 3)

        options = {
            included['id']: included['attributes']
            for included in self.response.json()['included']
            if included['type'] == 'polls/options'
        }
        self.assertEqual(options[str(self.option.pk)]['votes'], 2)
        self.assertEqual(options[str(self.option.pk)]['percentage'], 67)
        self.assertTrue(options[str(self.option.pk)]['winner'])
        self.assertEqual(options[str(other.pk)]['votes'], 1)
        self.assertEqual(options[str(other.pk)]['percentage'], 33)
        self.assertFalse(options[str(other.pk)]['winner'])

    def test_get_open_poll_omits_option_results(self):
        PollVoteFactory.create(poll=self.poll, option=self.option)
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        option = [
            included for included in self.response.json()['included']
            if included['type'] == 'polls/options'
        ][0]
        self.assertIsNone(option['attributes']['votes'])
        self.assertIsNone(option['attributes']['percentage'])
        self.assertIsNone(option['attributes']['winner'])

    def test_get_draft_poll(self):
        self.poll.status = 'draft'
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


class PollVoteExportViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.poll = PollFactory.create(status='open', title='Favourite colour')
        self.option = PollOptionFactory.create(poll=self.poll, title='Blue')
        self.votes = PollVoteFactory.create_batch(
            3, poll=self.poll, option=self.option
        )
        self.staff = BlueBottleUserFactory.create(is_staff=True)
        self.url = reverse('poll-detail', args=(self.poll.pk,))

    @property
    def export_url(self):
        if self.response and self.response.json()['data']['attributes']['results-export-url']:
            return self.response.json()['data']['attributes']['results-export-url']['url']

    def test_get_staff(self):
        self.perform_get(user=self.staff)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url)

        sheet = load_workbook(filename=io.BytesIO(response.content)).get_active_sheet()
        rows = list(sheet.values)
        self.assertEqual(
            rows[0], ('Name', 'Email', 'Date', 'Option')
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1][3], 'Blue')

    def test_get_staff_incorrect_hash(self):
        self.perform_get(user=self.staff)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url + 'test')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_regular_user(self):
        self.perform_get(user=self.user)
        self.assertIsNone(self.export_url)

    def test_get_no_user(self):
        self.perform_get()
        self.assertIsNone(self.export_url)

    def test_get_exports_disabled(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = False
        initiative_settings.save()
        self.perform_get(user=self.staff)
        self.assertIsNone(self.export_url)


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

    def test_list_own_votes(self):
        own = PollVoteFactory.create(
            poll=self.poll, option=self.option, owner=self.user
        )
        PollVoteFactory.create(poll=self.poll, option=self.other_option)
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(len(self.response.json()['data']), 1)
        self.assertEqual(self.response.json()['data'][0]['id'], str(own.pk))
        self.assertIncluded('poll', self.poll)
        self.assertIncluded('option', self.option)

    def test_list_includes_closed_poll_results(self):
        closed_poll = PollFactory.create(status='closed', title='Closed poll')
        winning = PollOptionFactory.create(poll=closed_poll, title='Winning')
        losing = PollOptionFactory.create(poll=closed_poll, title='Losing')
        PollVoteFactory.create(
            poll=closed_poll, option=winning, owner=self.user
        )
        PollVoteFactory.create(poll=closed_poll, option=winning)
        PollVoteFactory.create(poll=closed_poll, option=losing)

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        options = {
            included['id']: included['attributes']
            for included in self.response.json()['included']
            if included['type'] == 'polls/options'
            and included['id'] in {str(winning.pk), str(losing.pk)}
        }
        self.assertEqual(options[str(winning.pk)]['votes'], 2)
        self.assertTrue(options[str(winning.pk)]['winner'])
        self.assertEqual(options[str(losing.pk)]['votes'], 1)
        self.assertFalse(options[str(losing.pk)]['winner'])

    def test_list_filter_by_status(self):
        closed_poll = PollFactory.create(status='closed')
        closed_option = PollOptionFactory.create(poll=closed_poll)
        PollVoteFactory.create(
            poll=self.poll, option=self.option, owner=self.user
        )
        closed_vote = PollVoteFactory.create(
            poll=closed_poll, option=closed_option, owner=self.user
        )

        self.perform_get(user=self.user, query={'filter[status]': 'closed'})
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(len(self.response.json()['data']), 1)
        self.assertEqual(
            self.response.json()['data'][0]['id'], str(closed_vote.pk)
        )

    def test_list_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

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
