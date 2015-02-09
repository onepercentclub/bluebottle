import datetime
import json
from django.test import TestCase
from rest_framework import status
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.suggestions import SuggestionFactory
from bluebottle.test.factory_models.projects import ProjectFactory

from bluebottle.test.utils import InitProjectDataMixin
from bluebottle.suggestions.models import Suggestion

class SuggestionsIntegrationTest(InitProjectDataMixin, TestCase):
    """
    Integration tests for the Suggestion API.
    """
    def setUp(self):
        self.init_projects()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.suggestion = SuggestionFactory.create()
        self.suggestion_list_url = "/api/suggestions/"

    def tearDown(self):
        self.client.logout()

    def test_unauthenticated_user(self):
        """ Test that unauthenticated users get a 401 unauthorized response """
        response = self.client.get(self.suggestion_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    

    def test_retrieve_suggestion_list_status(self):
        """
        Test the status when retrieving all suggestions
        """
        response = self.client.get(self.suggestion_list_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_suggestion_list_all_items(self):
        """
        Test if all suggestions are retrieved
        """
        suggestion_2 = SuggestionFactory.create()
        suggestion_3 = SuggestionFactory.create()

        response = self.client.get(self.suggestion_list_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), Suggestion.objects.count())

    def test_retrieve_only_suggestions_with_destination(self):
        """
        Test the destination filter on the API endpoint. 
        """
        destination = 'amsterdam'

        suggestion_amsterdam_1 = SuggestionFactory.create(destination="Amsterdam")        
        suggestion_amsterdam_2 = SuggestionFactory.create(destination="amsterdam")

        response = self.client.get(self.suggestion_list_url, {'destination': destination},
                                    HTTP_AUTHORIZATION=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['destination'].lower(), destination)
        self.assertEqual(data[1]['destination'].lower(), destination)

    def test_retrieve_only_suggestions_with_status(self):
        """
        Test the status filter on the API endpoint. 
        """
        status = 'accepted'
        
        suggestion_accepted_1 = SuggestionFactory.create(status=status)        
        suggestion_accepted_2 = SuggestionFactory.create(status=status)
        suggestion_other = SuggestionFactory.create(status='other')


        response = self.client.get(self.suggestion_list_url, {'status': status},
                                    HTTP_AUTHORIZATION=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['status'].lower(), status)
        self.assertEqual(data[1]['status'].lower(), status)

    def test_retrieve_only_suggestions_with_project_slug(self):
        """
        Test the project slug filter on the API endpoint. Should return one suggestion
        """
        project = ProjectFactory.create()
        suggestion_accepted_1 = SuggestionFactory.create(project=project)        

        response = self.client.get(self.suggestion_list_url, {'project_slug': project.slug},
                                    HTTP_AUTHORIZATION=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

        self.assertEqual(data[0]['project'].lower(), project.slug)

    def test_retrieve_no_suggestions_with_fake_project_slug(self):
        """
        Test the project slug filter on the API endpoint. Shouldn't return any suggestions
        """
        project = ProjectFactory.create()
        suggestion_accepted_1 = SuggestionFactory.create(project=project)        

        response = self.client.get(self.suggestion_list_url, {'project_slug': "non-existing-slug"},
                                    HTTP_AUTHORIZATION=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(len(data), 0)



