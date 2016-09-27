import json
import re

from bluebottle.tasks.models import Task

from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey, Question, Response, Answer, SubQuestion


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
        question_re = re.compile("\[question\((\d+)\)\]")
        for key in data:
            match = question_re.match(key)
            if match:
                question = match.group(1)
                if bool(data[key]):
                    answers[question] = data[key]
        question_re = re.compile("\[question\((\d+)\)\,\ option.*\]")

        # Get question with multiple answers (return an array)
        for key in data:
            match = question_re.match(key)
            if match:
                question = match.group(1)
                if question not in answers:
                    answers[question] = []
                if data[key]:
                    answers[question].append(data[key])

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
        data = self.client.api.surveyresponse.filter('status', '=', 'Complete').list(survey.remote_id)
        self.client.config.response_type = None
        data = json.loads(data)
        # FIXME: Handle pagination BB-8029
        if int(data['total_count']) > 50:
            raise ImportWarning('There are more then 50 results, please also load page 2.')
        return data['data']

    def parse_question(self, data, survey):
        props = {}
        sub_questions = []
        if 'options' in data:
            props['options'] = [p['title']['English'] for p in data['options']]

        # Collect sub_questions
        if data['sub_question_skus']:
            for sub_id in data['sub_question_skus']:
                sub = self.client.api.surveyquestion.get(survey.remote_id, sub_id)
                sub_questions.append((sub_id, sub['data']['title']['English']))

        # Collect relevant properties (specified above)
        for p in self.question_properties:
            if p in data['properties'] and data['properties'][p]:
                props[p] = data['properties'][p]
            if p in data['properties']['messages'] and data['properties']['messages'][p]:
                props[p] = data['properties']['messages'][p]['English']

        question = {
            'title': data['title']['English'],
            'type': data['properties']['map_key'],
            'properties': props,
            'sub_questions': sub_questions
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
                    details = self.parse_question(quest, survey)
                    sub_questions = details.pop('sub_questions')
                    question, _created = Question.objects.update_or_create(
                        remote_id=quest['id'], survey=survey,
                        defaults=details
                    )
                    for sub_id, sub_title in sub_questions:
                        SubQuestion.objects.update_or_create(
                            question=question,
                            remote_id=sub_id,
                            defaults={'title': sub_title}
                        )

        for response in self.get_responses(survey):
            resp, created = Response.objects.update_or_create(
                remote_id=response['responseID'],
                survey=survey,
                defaults={
                    'specification': response,
                    'submitted': response['datesubmitted']
                }
            )
            params = self.parse_query_params(response)
            # Store all params
            resp.params = params

            # Find and store project/task
            try:
                resp.project = Project.objects.get(pk=int(params['project_id']))
            except (KeyError, Project.DoesNotExist):
                pass
            try:
                resp.task = Task.objects.get(pk=int(params['task_id']))
            except (KeyError, Task.DoesNotExist):
                pass

            try:
                resp.user_type = params['user_type']
            except AttributeError:
                pass

            resp.save()

            answers = self.parse_answers(response)
            for key in answers:
                question = None
                try:
                    question = Question.objects.get(remote_id=key, survey=survey)
                    # If it's a list then store it in options
                    if isinstance(answers[key], list):
                        answer_data = {'options': answers[key]}
                    else:
                        answer_data = {'value': answers[key]}
                    Answer.objects.update_or_create(response=resp, question=question,
                                                    defaults=answer_data)
                except Question.DoesNotExist:
                    try:
                        sub_question = SubQuestion.objects.get(remote_id=key, question__survey=survey)
                        answer, _c = Answer.objects.update_or_create(response=resp,
                                                                     question=sub_question.question)
                        options = answer.options or {}
                        options[sub_question.title] = int("0" + answers[key])
                        answer.options = options
                        answer.save()
                    except SubQuestion.DoesNotExist:
                        pass

        survey.aggregate()

    def get_survey(self, remote_id):
        return self.client.api.survey.get(remote_id)['data']
