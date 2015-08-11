import json

from django.core.urlresolvers import reverse

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.votes import VoteFactory


class ProjectVotesAPITestcase(BluebottleTestCase):
    """
    Base class for ``projects`` app API endpoints test cases.

    Sets up a common set of three ``Project``s and three ``ProjectTheme``s,
    as well as a dummy testing user which can be used for unit tests.
    """
    def setUp(self):
        super(ProjectVotesAPITestcase, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.project = ProjectFactory.create(owner=self.user)
        self.vote_url = reverse('project_votes_list', kwargs={'project_id': self.project.id})

    def test_vote(self):
        response = self.client.post(self.vote_url, {}, token=self.user_token)
        self.assertEqual(response.status_code, 201)

    def test_vote_project_does_not_exist(self):
        vote_url = reverse('project_votes_list', kwargs={'project_id': 1234})
        response = self.client.post(vote_url, {}, token=self.user_token)
        self.assertEqual(response.status_code, 404)

    def test_vote_unauthenticated(self):
        response = self.client.post(self.vote_url, {})
        self.assertEqual(response.status_code, 403)

    def test_vote_twice(self):
        self.client.post(self.vote_url, {}, token=self.user_token)
        response = self.client.post(self.vote_url, {}, token=self.user_token)
        self.assertEqual(response.status_code, 400)

    def test_get_votes(self):
        for i in range(11):
            user = BlueBottleUserFactory.create()
            VoteFactory.create(voter=user, project=self.project)

        response = self.client.get(self.vote_url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 11)
        self.assertEqual(len(data['results']), 10)

    def test_get_user_votes(self):
        for i in range(11):
            user = BlueBottleUserFactory.create()
            VoteFactory.create(voter=user, project=self.project)

        VoteFactory.create(voter=self.user, project=self.project)

        vote_url = self.vote_url + '?voter_id={}'.format(self.user.id)
        response = self.client.get(vote_url)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)
