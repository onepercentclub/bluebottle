import json
from urlparse import parse_qs

from httmock import HTTMock, urlmatch
from django.test.utils import override_settings
from django.utils import timezone

from bluebottle.surveys.adapters import SurveyGizmoAdapter
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.surveys import SurveyFactory


@urlmatch(path=r'.*\/survey\/test-id$')
def survey_mock(url, request):
    assert 'api_token_secret=test-secret' in url.query
    assert 'api_token=test-token' in url.query

    with open('bluebottle/surveys/tests/data/survey.json') as survey_file:
        return {
            'status_code': 200,
            'content': survey_file.read()
        }


@urlmatch(path=r'.*\/survey\/test-id/surveyquestion/.*$')
def survey_question_mock(url, request):
    question_id = url.path.split('/')[-1]
    with open('bluebottle/surveys/tests/data/survey_question_{}.json'.format(question_id)) as question_file:
        return {
            'status_code': 200,
            'content': question_file.read()
        }


def survey_response_mock(project, task):
    project_id = project.id
    task_id = task.id

    @urlmatch(path=r'.*\/survey\/test-id/surveyresponse/.*$')
    def survey_response_mock(url, request):
        page = parse_qs(url.query)['page'][0]
        with open('bluebottle/surveys/tests/data/survey_responses_page_{}.json'.format(page)) as response_file:
            data = json.load(response_file)
            for response in data['data']:
                response['[url("project_id")]'] = project_id
                response['[url("task_id")]'] = task_id

            return {
                'status_code': 200,
                'content': json.dumps(data)
            }
    return survey_response_mock


class TestSurveyGizmoAdapter(BluebottleTestCase):
    """
    """
    def setUp(self):
        super(TestSurveyGizmoAdapter, self).setUp()

        self.init_projects()

        self.theme = ProjectThemeFactory(slug='test-theme')
        self.project = ProjectFactory()

        self.task = TaskFactory(project=self.project)

        self.survey = SurveyFactory(remote_id='test-id', last_synced=timezone.now())

    @override_settings(
        SURVEYGIZMO_API_TOKEN='test-token',
        SURVEYGIZMO_API_SECRET='test-secret'
    )
    def test_update(self):
        adapter = SurveyGizmoAdapter()
        with HTTMock(survey_mock, survey_question_mock, survey_response_mock(self.project, self.task)):
            adapter.update_survey(self.survey)

        # There should now be 12 questions
        self.assertEqual(len(self.survey.question_set.all()), 12)
        # The project should have 2 response objects
        self.assertEqual(len(self.project.response_set.all()), 7)
        # All questions should be aggregated
        self.assertEqual(
            len(self.project.aggregateanswer_set.all()),
            15
        )

        self.assertTrue(self.survey.last_synced)
