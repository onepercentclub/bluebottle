import datetime

import json
from urlparse import parse_qs

from httmock import HTTMock, urlmatch
from django.test.utils import override_settings
from django.utils import timezone

from bluebottle.surveys.models import Question
from bluebottle.surveys.adapters import SurveyGizmoAdapter
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.surveys import (
    SurveyFactory, QuestionFactory, AnswerFactory, ResponseFactory, SubQuestionFactory
)


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


@override_settings(
    SURVEYGIZMO_API_TOKEN='test-token',
    SURVEYGIZMO_API_SECRET='test-secret'
)
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


@override_settings(
    SURVEYGIZMO_API_TOKEN='test-token',
    SURVEYGIZMO_API_SECRET='test-secret'
)
class PlatformAggregateTest(BluebottleTestCase):
    def setUp(self):
        super(PlatformAggregateTest, self).setUp()
        now = timezone.now()
        last_year = now - datetime.timedelta(days=365)

        self.init_projects()

        survey = SurveyFactory.create()

        old_project = ProjectFactory.create(campaign_ended=last_year)
        new_project = ProjectFactory.create(campaign_ended=now)

        old_task1 = TaskFactory.create(project=old_project)
        old_task2 = TaskFactory.create(project=new_project)

        question1 = QuestionFactory.create(remote_id=1, type='number', survey=survey)
        question2 = QuestionFactory.create(remote_id=2, type='table-radio', survey=survey)
        SubQuestionFactory.create(question=question2, title='before')
        SubQuestionFactory.create(question=question2, title='after')
        question3 = QuestionFactory.create(remote_id=3, type='checkbox', survey=survey)
        question4 = QuestionFactory.create(remote_id=4, type='number', aggregation='average', survey=survey)

        for answer1, answer2, answer3, answer4 in (
            (4, {'before': 1, 'after': 3}, {'test': 3, 'tast': 4}, 62),
            (6, {'before': 3, 'after': 5}, {'test': 4, 'tast': 3}, 65),
            (8, {'before': 5, 'after': 5}, {'test': 5, 'tast': 5}, 55),
            (2, {'before': 7, 'after': 3}, {'test': 6, 'tast': 5}, 62)
        ):
            response = ResponseFactory(project=old_project, survey=survey)
            AnswerFactory.create(question=question1, response=response, value=answer1)
            AnswerFactory.create(question=question2, response=response, options=answer2)
            AnswerFactory.create(question=question3, response=response, options=answer3)
            AnswerFactory.create(question=question4, response=response, value=answer4)

        for answer1, answer2, answer3, answer4 in (
            (2, {'before': 6, 'after': 8}, {'test': 4, 'tast': 5}, 60),
            (4, {'before': 2, 'after': 4}, {'test': 4, 'tast': 2}, 40),
        ):
            response = ResponseFactory(task=old_task1, survey=survey)
            AnswerFactory.create(question=question1, response=response, value=answer1)
            AnswerFactory.create(question=question2, response=response, options=answer2)
            AnswerFactory.create(question=question3, response=response, options=answer3)
            AnswerFactory.create(question=question4, response=response, value=answer4)

        for answer1, answer2, answer3, answer4 in (
            (11, {'before': 0, 'after': 2}, {'test': 2, 'tast': 3}, 12),
            (9, {'before': 2, 'after': 4}, {'test': 4, 'tast': 2}, 16),
        ):
            response = ResponseFactory(task=old_task2, survey=survey)
            AnswerFactory.create(question=question1, response=response, value=answer1)
            AnswerFactory.create(question=question2, response=response, options=answer2)
            AnswerFactory.create(question=question3, response=response, options=answer3)
            AnswerFactory.create(question=question4, response=response, value=answer4)

        for answer1, answer2, answer3, answer4 in (
            (3, {'before': 0, 'after': 2}, {'test': 2, 'tast': 3}, 23),
            (5, {'before': 2, 'after': 4}, {'test': 4, 'tast': 2}, 12),
            (7, {'before': 5, 'after': 4}, {'test': 4, 'tast': 5}, 14),
            (1, {'before': 6, 'after': 2}, {'test': 5, 'tast': 4}, 500)
        ):
            response = ResponseFactory(project=new_project, survey=survey)
            AnswerFactory.create(question=question1, response=response, value=answer1)
            AnswerFactory.create(question=question2, response=response, options=answer2)
            AnswerFactory.create(question=question3, response=response, options=answer3)
            AnswerFactory.create(question=question4, response=response, value=answer4)

        survey.aggregate()

    def test_platform_answers(self):
        expected_result = {
            '1': 13.0,
            '2': {'after': 4.5, 'before': 2.5},
            '3': {u'test': 7.0, u'tast': 6.0},
            '4': 32.0
        }
        for question in Question.objects.all():
            aggregate = question.get_platform_aggregate()
            self.assertEqual(aggregate, expected_result[question.remote_id])

    def test_platform_answers_since_yesterday(self):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        expected_result = {
            '1': 10.0,
            '2': {'after': 3.0, 'before': 1.0},
            '3': {u'test': 6.0, u'tast': 5.0},
            '4': 14.0
        }
        for question in Question.objects.all():
            aggregate = question.get_platform_aggregate(start=yesterday)
            self.assertEqual(aggregate, expected_result[question.remote_id])

    def test_platform_answers_before_yesterday(self):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        expected_result = {
            '1': 3.0,
            '2': {'after': 6.0, 'before': 4.0},
            '3': {u'test': 8.0, u'tast': 7.0},
            '4': 50.0
        }
        for question in Question.objects.all():
            aggregate = question.get_platform_aggregate(end=yesterday)
            self.assertEqual(aggregate, expected_result[question.remote_id])
