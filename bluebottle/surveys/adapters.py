import json

from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.surveys.models import Survey, Question, Response


class BaseAdapter(object):

    def get_surveys(self):
        raise NotImplementedError()

    def update_surveys(self):
        for data in self.get_surveys():
            survey, created = Survey.objects.get_or_create(remote_id=data['id'])
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

    def get_responses(self, survey):
        self.client.config.response_type = 'json'
        data = self.client.api.surveyresponse.list(survey.remote_id)
        self.client.config.response_type = None
        data = json.loads(data)
        print data
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
                    Question.objects.get_or_create(
                        remote_id=quest['id'], survey=survey,
                        defaults=self.parse_question(quest)
                    )
        for response in self.get_responses(survey):
            Response.objects.get_or_create(remote_id=response['responseID'], survey=survey,
                                           defaults={'specification': json.dumps(response)})

    def get_surveys(self):
        return self.client.api.survey.list()['data']

    def get_survey(self, remote_id):
        return self.client.api.survey.get(remote_id)['data']

