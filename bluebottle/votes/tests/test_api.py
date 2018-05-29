import json


from django.core.urlresolvers import reverse

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.votes.models import Vote

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.votes import VoteFactory

from bluebottle.test.factory_models.categories import CategoryFactory


class ProjectVotesAPITestCase(BluebottleTestCase):
    """
    Base class for ``projects`` app API endpoints test cases.

    Sets up a common set of three ``Project``s and three ``ProjectTheme``s,
    as well as a dummy testing user which can be used for unit tests.
    """

    def setUp(self):
        super(ProjectVotesAPITestCase, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        phase = ProjectPhase.objects.get(slug='voting')

        self.project1 = ProjectFactory.create(owner=self.user, status=phase)
        self.project2 = ProjectFactory.create(owner=self.user, status=phase)
        self.project3 = ProjectFactory.create(owner=self.user, status=phase)
        self.vote_url = reverse('vote_list')

    def test_vote(self):
        response = self.client.post(self.vote_url,
                                    {'project': self.project1.slug},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        vote = Vote.objects.all()[0]

        self.assertEqual(vote.project, self.project1)
        self.assertEqual(vote.voter, self.user)
        self.assertEqual(vote.ip_address, '127.0.0.1')

    def test_vote_project_does_not_exist(self):
        response = self.client.post(self.vote_url,
                                    {'project': 'none-existing-project'},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['project'][0],
                         "Object with slug=none-existing-project does not exist.")

    def test_vote_unauthenticated(self):
        response = self.client.post(self.vote_url,
                                    {'project': self.project1.slug})
        self.assertEqual(response.status_code, 401)

    def test_vote_twice(self):
        self.client.post(self.vote_url,
                         {'project': self.project1.slug}, token=self.user_token)
        response = self.client.post(self.vote_url,
                                    {'project': self.project1.slug},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            unicode(response.data['non_field_errors'][0]), 'You already voted.'
        )

    def test_vote_on_second_project(self):
        self.client.post(self.vote_url, {'project': self.project1.slug},
                         token=self.user_token)
        response = self.client.post(self.vote_url,
                                    {'project': self.project2.slug},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)

    def test_vote_on_second_project_in_same_cateogry(self):
        category = CategoryFactory.create()

        self.project1.categories = [category]
        self.project1.save()

        self.project2.categories = [category]
        self.project2.save()

        self.client.post(self.vote_url, {'project': self.project1.slug},
                         token=self.user_token)
        response = self.client.post(self.vote_url,
                                    {'project': self.project2.slug},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            unicode(response.data['non_field_errors'][0]), u'You already voted.'
        )

    def test_vote_already_votes_twice(self):
        category = CategoryFactory.create()

        self.project1.categories = [category]
        self.project1.save()

        self.project2.categories = [category]
        self.project2.save()

        self.project3.categories = [category]
        self.project3.save()

        VoteFactory.create(voter=self.user, project=self.project1)
        VoteFactory.create(voter=self.user, project=self.project2)

        response = self.client.post(self.vote_url,
                                    {'project': self.project3.slug},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            unicode(response.data['non_field_errors'][0]), u'You already voted.'
        )

    def test_get_votes(self):
        VoteFactory.create_batch(11, project=self.project1)
        VoteFactory.create_batch(12, project=self.project2)

        response = self.client.get(self.vote_url +
                                   '?project={0}'.format(self.project1.slug))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 11)
        self.assertEqual(len(data['results']), 10)

    def test_get_user_votes(self):
        VoteFactory.create_batch(11, project=self.project1)
        VoteFactory.create_batch(3, project=self.project2)
        VoteFactory.create(voter=self.user, project=self.project1)
        VoteFactory.create(voter=self.user, project=self.project2)

        vote_url = self.vote_url + '?voter={0}'.format(self.user.id)
        response = self.client.get(vote_url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)
