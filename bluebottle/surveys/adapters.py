import json
import re

from bluebottle.tasks.models import Task
from django.db.models import Sum, Avg

from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey, Question, Response, Answer, AggregateAnswer


class BaseAdapter(object):

    def get_surveys(self):
        return Survey.objects.all()

    def update_surveys(self):
        for survey in self.get_surveys():
            self.update_survey(survey)

    def update_survey(self, remote_id):
        raise NotImplementedError()

    def get_survey(self, remote_id):
        raise NotImplementedError()


class SurveyGizmoAdapter(BaseAdapter):

    question_properties = ['left_label', 'center_label', 'right_label',
                           'min_number', 'max_number']

    def __init__(self):
        self.client = SurveyGizmo(
            api_version='v4',
            api_token=properties.SURVEYGIZMO_API_TOKEN,
            api_token_secret=properties.SURVEYGIZMO_API_SECRET
        )

    def parse_answers(self, data):
        answers = {}
        question_re = re.compile("\[question\((\d+)\).*\]")
        for key in data:
            match = question_re.match(key)
            if match:
                question = match.group(1)
                if answers.has_key(question):
                    answers[question] += ", " + data[key]
                else:
                    answers[question] = data[key]
        return answers

    def parse_query_params(self, data):
        params = {}
        query_param_re = re.compile("\[url\(\"(.+)\"\)]")
        for key in data:
            match = query_param_re.match(key)
            if match:
                param = match.group(1)
                params[param] = data[key]
        return params

    def get_responses(self, survey):
        self.client.config.response_type = 'json'
        data = self.client.api.surveyresponse.list(survey.remote_id)
        self.client.config.response_type = None
        data = json.loads(data)
        if int(data['total_count']) > 50:
            raise ImportWarning('There are more then 50 results, please also load page 2.')
        return data['data']

    def parse_question(self, data):
        props = {}
        if data.has_key('options'):
            props['options'] = [p['title']['English'] for p in data['options']]

        for p in self.question_properties:
            if data['properties'].has_key(p):
                props[p] = data['properties'][p]

        question = {
            'title': data['title']['English'],
            'type': data['properties']['map_key'],
            'properties': props
        }
        return question

    def update_survey(self, survey):
        data = self.get_survey(survey.remote_id)
        survey.specification = data
        survey.title = data['title']
        survey.link = data['links']['campaign']
        survey.save()

        for page in data['pages']:
            for quest in page['questions']:
                if quest['_type'] == 'SurveyQuestion':
                    Question.objects.update_or_create(
                        remote_id=quest['id'], survey=survey,
                        defaults=self.parse_question(quest)
                    )
        for response in self.get_responses(survey):
            resp, created = Response.objects.update_or_create(
                remote_id=response['responseID'],
                survey=survey,
                defaults={'specification': response}
            )
            params = self.parse_query_params(response)
            if params.has_key('project_id') and params['project_id']:
                try:
                    resp.project = Project.objects.get(pk=int(params['project_id']))
                except Project.DoesNotExist:
                    pass
            if params.has_key('task_id') and params['task_id']:
                try:
                    resp.task = Task.objects.get(pk=int(params['task_id']))
                except Task.DoesNotExist:
                    pass
            resp.save()

            answers = self.parse_answers(response)
            for key in answers:
                try:
                    question = Question.objects.get(remote_id=key, survey=survey)
                    Answer.objects.update_or_create(response=resp, question=question,
                                                 defaults={'value': answers[key]})
                except Question.DoesNotExist:
                    pass
        survey.aggregate()

    def get_survey(self, remote_id):
        return self.client.api.survey.get(remote_id)['data']

