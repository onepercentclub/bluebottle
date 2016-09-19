from bluebottle.clients import properties
from surveygizmo import SurveyGizmo

from bluebottle.surveys.models import Survey


class BaseAdapter(object):

    def get_surveys(self):
        raise NotImplementedError()

    def update_surveys(self):
        for surv in self.get_surveys():
            Survey.objects.get_or_create(remote_id=surv.id, defaults={'specification': surv})


class SurveyGizmoAdapter(BaseAdapter):

    def __init__(self):
        self.client = SurveyGizmo(
            api_version='v4',
            api_token = properties.SURVEYGIZMO_API_TOKEN,
            api_token_secret = properties.SURVEYGIZMO_API_SECRET
        )

    def get_surveys(self):
        return self.client.api.survey.list()